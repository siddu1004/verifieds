#ifndef SIM_SCHEDULER_HPP
#define SIM_SCHEDULER_HPP

#include "CircularQueue.hpp"
#include "DynArray.hpp"
#include "Process.hpp"
#include "ReadyQueue.hpp"
#include <cmath>
#include <cstddef>
#include <stdexcept>

struct GanttSlice {
    int pid{-1}; // -1 for idle time
    int start{0};
    int end{0};

    bool operator==(const GanttSlice& other) const noexcept {
        return pid == other.pid && start == other.start && end == other.end;
    }
};

struct ProcessMetrics {
    int pid{0};
    int completion{0};
    int turnaround{0};
    int waiting{0};
    int response{0};

    bool operator==(const ProcessMetrics& other) const noexcept {
        return pid == other.pid && completion == other.completion &&
               turnaround == other.turnaround && waiting == other.waiting &&
               response == other.response;
    }
};

struct ScheduleResult {
    DynArray<GanttSlice> gantt{};
    DynArray<ProcessMetrics> metrics{};
    double avg_waiting{0.0};
    double avg_turnaround{0.0};
    double avg_response{0.0};

    bool operator==(const ScheduleResult& other) const noexcept {
        if (gantt.size() != other.gantt.size() || metrics.size() != other.metrics.size()) return false;
        for (std::size_t i = 0; i < gantt.size(); ++i) {
            if (!(gantt[i] == other.gantt[i])) return false;
        }
        for (std::size_t i = 0; i < metrics.size(); ++i) {
            if (!(metrics[i] == other.metrics[i])) return false;
        }
        return std::abs(avg_waiting - other.avg_waiting) < 0.005 &&
               std::abs(avg_turnaround - other.avg_turnaround) < 0.005 &&
               std::abs(avg_response - other.avg_response) < 0.005;
    }
};

namespace detail {

inline void add_gantt_slice(DynArray<GanttSlice>& gantt, int pid, int start, int end) {
    if (start >= end) return;
    if (!gantt.empty() && gantt[gantt.size() - 1].pid == pid) {
        gantt[gantt.size() - 1].end = end;
    } else {
        gantt.push_back(GanttSlice{pid, start, end});
    }
}

struct ProcState {
    Process p{};
    int remaining{0};
    int first_start{-1};
    int completion{-1};
    bool started{false};
    bool finished{false};
};

inline ScheduleResult build_result(const DynArray<GanttSlice>& gantt, DynArray<ProcState>& states) {
    // Sort states by PID using simple stable insertion sort
    for (std::size_t i = 1; i < states.size(); ++i) {
        ProcState key = states[i];
        std::size_t j = i;
        while (j > 0 && states[j - 1].p.pid > key.p.pid) {
            states[j] = states[j - 1];
            --j;
        }
        states[j] = key;
    }

    DynArray<ProcessMetrics> metrics;
    double sum_wait = 0.0;
    double sum_tat = 0.0;
    double sum_resp = 0.0;
    std::size_t n = states.size();

    for (std::size_t i = 0; i < n; ++i) {
        const auto& s = states[i];
        int turnaround = s.completion - s.p.arrival;
        int waiting = turnaround - s.p.burst;
        int response = s.first_start - s.p.arrival;

        metrics.push_back(ProcessMetrics{
            s.p.pid,
            s.completion,
            turnaround,
            waiting,
            response
        });

        sum_wait += waiting;
        sum_tat += turnaround;
        sum_resp += response;
    }

    double avg_w = n > 0 ? sum_wait / static_cast<double>(n) : 0.0;
    double avg_t = n > 0 ? sum_tat / static_cast<double>(n) : 0.0;
    double avg_r = n > 0 ? sum_resp / static_cast<double>(n) : 0.0;

    return ScheduleResult{gantt, metrics, avg_w, avg_t, avg_r};
}

enum class PolicyType { FCFS, SJF, PRIORITY };

inline ScheduleResult run_non_preemptive(const DynArray<Process>& processes, ReadyQueue& queue, PolicyType policy) {
    validate_processes(processes);
    if (processes.empty()) {
        return ScheduleResult{DynArray<GanttSlice>{}, DynArray<ProcessMetrics>{}, 0.0, 0.0, 0.0};
    }

    queue.clear();
    DynArray<ProcState> states;
    DynArray<bool> queued;
    for (std::size_t i = 0; i < processes.size(); ++i) {
        states.push_back(ProcState{processes[i], processes[i].burst, -1, -1, false, false});
        queued.push_back(false);
    }

    DynArray<GanttSlice> gantt;
    int current_time = 0;
    std::size_t completed_count = 0;
    std::size_t n = processes.size();

    auto get_key = [policy](const Process& p) -> long {
        if (policy == PolicyType::FCFS) return p.arrival;
        if (policy == PolicyType::SJF) return p.burst;
        return p.priority;
    };

    while (completed_count < n) {
        // Enqueue all arrived processes
        for (std::size_t i = 0; i < n; ++i) {
            if (!queued[i] && !states[i].finished && states[i].p.arrival <= current_time) {
                queue.push(ReadyEntry{get_key(states[i].p), states[i].p.arrival, states[i].p.pid});
                queued[i] = true;
            }
        }

        if (queue.empty()) {
            // Find earliest arrival among remaining processes
            int next_arrival = -1;
            for (std::size_t i = 0; i < n; ++i) {
                if (!states[i].finished) {
                    if (next_arrival == -1 || states[i].p.arrival < next_arrival) {
                        next_arrival = states[i].p.arrival;
                    }
                }
            }
            if (next_arrival > current_time) {
                add_gantt_slice(gantt, -1, current_time, next_arrival);
                current_time = next_arrival;
            }
            // Enqueue processes arriving at next_arrival
            for (std::size_t i = 0; i < n; ++i) {
                if (!queued[i] && !states[i].finished && states[i].p.arrival <= current_time) {
                    queue.push(ReadyEntry{get_key(states[i].p), states[i].p.arrival, states[i].p.pid});
                    queued[i] = true;
                }
            }
        }

        ReadyEntry entry = queue.pop_min();
        // Find index of process
        std::size_t idx = 0;
        for (std::size_t i = 0; i < n; ++i) {
            if (states[i].p.pid == entry.pid) {
                idx = i;
                break;
            }
        }

        ProcState& s = states[idx];
        if (!s.started) {
            s.started = true;
            s.first_start = current_time;
        }

        int start_time = current_time;
        current_time += s.p.burst;
        s.completion = current_time;
        s.finished = true;
        ++completed_count;

        add_gantt_slice(gantt, s.p.pid, start_time, current_time);
    }

    return build_result(gantt, states);
}

} // namespace detail

inline ScheduleResult run_fcfs(const DynArray<Process>& processes, ReadyQueue& queue) {
    return detail::run_non_preemptive(processes, queue, detail::PolicyType::FCFS);
}

inline ScheduleResult run_sjf(const DynArray<Process>& processes, ReadyQueue& queue) {
    return detail::run_non_preemptive(processes, queue, detail::PolicyType::SJF);
}

inline ScheduleResult run_priority(const DynArray<Process>& processes, ReadyQueue& queue) {
    return detail::run_non_preemptive(processes, queue, detail::PolicyType::PRIORITY);
}

inline ScheduleResult run_srtf(const DynArray<Process>& processes, ReadyQueue& queue) {
    validate_processes(processes);
    if (processes.empty()) {
        return ScheduleResult{DynArray<GanttSlice>{}, DynArray<ProcessMetrics>{}, 0.0, 0.0, 0.0};
    }

    queue.clear();
    DynArray<detail::ProcState> states;
    DynArray<bool> queued;
    for (std::size_t i = 0; i < processes.size(); ++i) {
        states.push_back(detail::ProcState{processes[i], processes[i].burst, -1, -1, false, false});
        queued.push_back(false);
    }

    DynArray<GanttSlice> gantt;
    int current_time = 0;
    std::size_t completed_count = 0;
    std::size_t n = processes.size();

    int active_pid = -1;
    std::size_t active_idx = 0;

    while (completed_count < n) {
        // Enqueue processes arriving at current_time
        for (std::size_t i = 0; i < n; ++i) {
            if (!queued[i] && !states[i].finished && states[i].p.arrival <= current_time) {
                queue.push(ReadyEntry{states[i].remaining, states[i].p.arrival, states[i].p.pid});
                queued[i] = true;
            }
        }

        // Check if active process should be preempted
        if (active_pid != -1) {
            if (!queue.empty()) {
                ReadyEntry best = queue.peek_min();
                if (best.key < states[active_idx].remaining) {
                    // Preempt active process
                    queue.push(ReadyEntry{states[active_idx].remaining, states[active_idx].p.arrival, states[active_idx].p.pid});
                    active_pid = -1;
                }
            }
        }

        // If no active process, pick from queue
        if (active_pid == -1) {
            if (!queue.empty()) {
                ReadyEntry entry = queue.pop_min();
                active_pid = entry.pid;
                for (std::size_t i = 0; i < n; ++i) {
                    if (states[i].p.pid == active_pid) {
                        active_idx = i;
                        break;
                    }
                }
                if (!states[active_idx].started) {
                    states[active_idx].started = true;
                    states[active_idx].first_start = current_time;
                }
            }
        }

        // Execute 1 unit of time
        if (active_pid != -1) {
            detail::add_gantt_slice(gantt, active_pid, current_time, current_time + 1);
            states[active_idx].remaining -= 1;
            if (states[active_idx].remaining == 0) {
                states[active_idx].finished = true;
                states[active_idx].completion = current_time + 1;
                ++completed_count;
                active_pid = -1;
            }
        } else {
            detail::add_gantt_slice(gantt, -1, current_time, current_time + 1);
        }

        current_time += 1;
    }

    return detail::build_result(gantt, states);
}

inline ScheduleResult run_round_robin(const DynArray<Process>& processes, int quantum) {
    if (quantum <= 0) {
        throw std::invalid_argument("Round Robin quantum must be > 0");
    }
    validate_processes(processes);
    if (processes.empty()) {
        return ScheduleResult{DynArray<GanttSlice>{}, DynArray<ProcessMetrics>{}, 0.0, 0.0, 0.0};
    }

    DynArray<detail::ProcState> states;
    DynArray<bool> queued;
    for (std::size_t i = 0; i < processes.size(); ++i) {
        states.push_back(detail::ProcState{processes[i], processes[i].burst, -1, -1, false, false});
        queued.push_back(false);
    }

    CircularQueue<int> cq(processes.size() + 2);
    DynArray<GanttSlice> gantt;
    int current_time = 0;
    std::size_t completed_count = 0;
    std::size_t n = processes.size();

    // Enqueue processes arriving at t = 0 (sorted by arrival, then pid)
    auto check_and_enqueue_arrivals = [&](int up_to_time) {
        while (true) {
            int earliest_arrival = -1;
            std::size_t best_idx = n;
            for (std::size_t i = 0; i < n; ++i) {
                if (!queued[i] && !states[i].finished && states[i].p.arrival <= up_to_time) {
                    if (earliest_arrival == -1 || states[i].p.arrival < earliest_arrival ||
                        (states[i].p.arrival == earliest_arrival && (best_idx == n || states[i].p.pid < states[best_idx].p.pid))) {
                        earliest_arrival = states[i].p.arrival;
                        best_idx = i;
                    }
                }
            }
            if (best_idx == n) break;
            cq.enqueue(states[best_idx].p.pid);
            queued[best_idx] = true;
        }
    };

    check_and_enqueue_arrivals(current_time);

    while (completed_count < n) {
        if (cq.empty()) {
            int next_arrival = -1;
            for (std::size_t i = 0; i < n; ++i) {
                if (!states[i].finished) {
                    if (next_arrival == -1 || states[i].p.arrival < next_arrival) {
                        next_arrival = states[i].p.arrival;
                    }
                }
            }
            if (next_arrival > current_time) {
                detail::add_gantt_slice(gantt, -1, current_time, next_arrival);
                current_time = next_arrival;
            }
            check_and_enqueue_arrivals(current_time);
        }

        int pid = cq.front();
        cq.dequeue();
        std::size_t idx = 0;
        for (std::size_t i = 0; i < n; ++i) {
            if (states[i].p.pid == pid) {
                idx = i;
                break;
            }
        }

        if (!states[idx].started) {
            states[idx].started = true;
            states[idx].first_start = current_time;
        }

        int slice = states[idx].remaining < quantum ? states[idx].remaining : quantum;
        int start_time = current_time;
        int end_time = current_time + slice;
        detail::add_gantt_slice(gantt, pid, start_time, end_time);

        states[idx].remaining -= slice;
        current_time = end_time;

        // Arrivals during execution up to end_time enter queue BEFORE re-enqueuing preempted process
        check_and_enqueue_arrivals(end_time);

        if (states[idx].remaining > 0) {
            cq.enqueue(pid);
        } else {
            states[idx].finished = true;
            states[idx].completion = current_time;
            ++completed_count;
        }
    }

    return detail::build_result(gantt, states);
}

#endif // SIM_SCHEDULER_HPP
