// Persistent thread pool reused across canonical_string calls.
//
// std::async with std::launch::async creates fresh threads per submission.
// For the canonical-string seed loop (15 seeds on the doily) that's 15
// thread creations + 15 joins per call. A pool with worker threads
// blocked on a condition variable avoids that overhead.
#pragma once

#include <atomic>
#include <condition_variable>
#include <cstddef>
#include <deque>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <thread>
#include <utility>
#include <vector>

namespace isalhg {

class ThreadPool {
public:
    explicit ThreadPool(std::size_t n_workers) {
        workers_.reserve(n_workers);
        for (std::size_t i = 0; i < n_workers; ++i) {
            workers_.emplace_back([this]() { worker_loop(); });
        }
    }

    ~ThreadPool() {
        {
            std::lock_guard<std::mutex> lock(mu_);
            stop_ = true;
        }
        cv_.notify_all();
        for (auto& t : workers_) t.join();
    }

    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

    template <typename F>
    auto submit(F&& f) -> std::future<decltype(f())> {
        using R = decltype(f());
        auto task = std::make_shared<std::packaged_task<R()>>(std::forward<F>(f));
        std::future<R> fut = task->get_future();
        {
            std::lock_guard<std::mutex> lock(mu_);
            queue_.emplace_back([task]() { (*task)(); });
        }
        cv_.notify_one();
        return fut;
    }

    [[nodiscard]] std::size_t size() const noexcept { return workers_.size(); }

private:
    void worker_loop() {
        for (;;) {
            std::function<void()> job;
            {
                std::unique_lock<std::mutex> lock(mu_);
                cv_.wait(lock, [this]() { return stop_ || !queue_.empty(); });
                if (stop_ && queue_.empty()) return;
                job = std::move(queue_.front());
                queue_.pop_front();
            }
            job();
        }
    }

    std::vector<std::thread> workers_;
    std::deque<std::function<void()>> queue_;
    std::mutex mu_;
    std::condition_variable cv_;
    bool stop_ = false;
};

// Process-wide pool sized to hardware_concurrency(). The first call
// blocks on thread creation; subsequent calls reuse the workers.
ThreadPool& canonical_thread_pool();

}  // namespace isalhg
