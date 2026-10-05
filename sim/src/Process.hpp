#ifndef SIM_PROCESS_HPP
#define SIM_PROCESS_HPP

#include "DynArray.hpp"
#include <stdexcept>

struct Process {
    int pid{0};
    int arrival{0};
    int burst{0};
    int priority{0};

    bool operator==(const Process& other) const noexcept {
        return pid == other.pid && arrival == other.arrival &&
               burst == other.burst && priority == other.priority;
    }
};

inline void validate_processes(const DynArray<Process>& processes) {
    for (std::size_t i = 0; i < processes.size(); ++i) {
        if (processes[i].burst <= 0) {
            throw std::invalid_argument("Process burst must be > 0");
        }
        if (processes[i].arrival < 0) {
            throw std::invalid_argument("Process arrival must be >= 0");
        }
        for (std::size_t j = i + 1; j < processes.size(); ++j) {
            if (processes[i].pid == processes[j].pid) {
                throw std::invalid_argument("Duplicate process pid detected");
            }
        }
    }
}

#endif // SIM_PROCESS_HPP
