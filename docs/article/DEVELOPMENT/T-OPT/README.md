# T-OPT — C++ encoder optimisations

Engineering tasks that improve the wall-clock performance or the operational
envelope of the C++ canonical encoder (`AlgorithmVariant::GreedyMinComplete = 7`)
without changing the value of `w*_c` (frozen by D-TA2).  Sanctioned speedups are
stabiliser-orbit pruning (Prop. 6.0, value-preserving) and runtime-parameter
generalisation.  Any change that modifies the canonical string definition is
forbidden and must be escalated to the PI.
