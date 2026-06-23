#include "isalhg/thread_pool.hpp"

#include <algorithm>

namespace isalhg {

ThreadPool& canonical_thread_pool() {
    static ThreadPool pool(std::max(1u, std::thread::hardware_concurrency()));
    return pool;
}

}  // namespace isalhg
