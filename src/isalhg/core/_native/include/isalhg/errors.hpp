// Exception hierarchy for the IsalHG native core.
//
// Translated back to the Python types in ``isalhg.errors`` at module init.
// Keeping C++ exceptions thin (a single what() string) avoids divergence
// from the Python hierarchy.
#pragma once

#include <stdexcept>
#include <string>

namespace isalhg {

struct IsalHGError : public std::runtime_error {
    using std::runtime_error::runtime_error;
};

struct H2SStuckError : public IsalHGError {
    using IsalHGError::IsalHGError;
};

struct DisconnectedHypergraphError : public IsalHGError {
    using IsalHGError::IsalHGError;
};

struct VocabularyMismatchError : public IsalHGError {
    using IsalHGError::IsalHGError;
};

struct CapacityError : public IsalHGError {
    using IsalHGError::IsalHGError;
};

struct InvalidLabelError : public IsalHGError {
    using IsalHGError::IsalHGError;
};

struct ArityMismatchError : public IsalHGError {
    using IsalHGError::IsalHGError;
};

struct InvalidInstructionError : public IsalHGError {
    using IsalHGError::IsalHGError;
};

}  // namespace isalhg
