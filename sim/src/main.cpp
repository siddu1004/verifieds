#include "BST.hpp"
#include "Config.hpp"
#include "DynArray.hpp"
#include "Process.hpp"
#include "ReadyQueue.hpp"
#include "Scheduler.hpp"
#include "Sort.hpp"
#include "Stack.hpp"

#include <cstdio>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>

struct PidIndex {
    int pid{0};
    std::size_t index{0};

    bool operator<(const PidIndex& other) const noexcept {
        return pid < other.pid;
    }
};

struct ContextSwitch {
    int from_pid{0};
    int to_pid{0};
    int time{0};
};

static void rebuild_bst(const DynArray<Process>& procs, BST<PidIndex>& bst) {
    bst = BST<PidIndex>{};
    for (std::size_t i = 0; i < procs.size(); ++i) {
        bst.insert(PidIndex{procs[i].pid, i});
    }
}

static Stack<ContextSwitch> extract_context_switches(const DynArray<GanttSlice>& gantt) {
    Stack<ContextSwitch> history;
    DynArray<GanttSlice> non_idle;
    for (std::size_t i = 0; i < gantt.size(); ++i) {
        if (gantt[i].pid != -1) {
            non_idle.push_back(gantt[i]);
        }
    }
    for (std::size_t i = 1; i < non_idle.size(); ++i) {
        if (non_idle[i].pid != non_idle[i - 1].pid) {
            history.push(ContextSwitch{non_idle[i - 1].pid, non_idle[i].pid, non_idle[i].start});
        }
    }
    return history;
}

static int count_context_switches(const DynArray<GanttSlice>& gantt) {
    int count = 0;
    DynArray<GanttSlice> non_idle;
    for (std::size_t i = 0; i < gantt.size(); ++i) {
        if (gantt[i].pid != -1) {
            non_idle.push_back(gantt[i]);
        }
    }
    for (std::size_t i = 1; i < non_idle.size(); ++i) {
        if (non_idle[i].pid != non_idle[i - 1].pid) {
            ++count;
        }
    }
    return count;
}

static int run_batch(const std::string& filepath) {
    std::ifstream infile(filepath);
    if (!infile.is_open()) {
        std::cerr << "Error: Cannot open batch file: " << filepath << "\n";
        return 2;
    }

    std::string policy;
    std::string backend(kDefaultBackend);
    int quantum = 0;
    int num_processes = -1;

    std::string line;
    while (std::getline(infile, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::size_t eq = line.find('=');
        if (eq != std::string::npos) {
            std::string key = line.substr(0, eq);
            std::string val = line.substr(eq + 1);
            if (key == "policy") policy = val;
            else if (key == "backend") backend = val;
            else if (key == "quantum") quantum = std::stoi(val);
            else if (key == "processes") {
                num_processes = std::stoi(val);
                break;
            }
        }
    }

    if (policy.empty() || num_processes < 0) {
        std::cerr << "Error: Malformed batch file header in " << filepath << "\n";
        return 2;
    }

    DynArray<Process> processes;
    for (int i = 0; i < num_processes; ++i) {
        if (!(infile >> line)) {
            std::cerr << "Error: Premature EOF reading process in batch file\n";
            return 2;
        }
        int pid = std::stoi(line);
        int arr = 0, burst = 0, prio = 0;
        if (!(infile >> arr >> burst >> prio)) {
            std::cerr << "Error: Malformed process entry in batch file\n";
            return 2;
        }
        processes.push_back(Process{pid, arr, burst, prio});
    }

    try {
        validate_processes(processes);
    } catch (const std::exception& err) {
        std::cerr << "Error: Process validation failed: " << err.what() << "\n";
        return 2;
    }

    ScheduleResult res;
    ArrayReadyQueue aq;
    HeapReadyQueue hq;
    ReadyQueue* q_ptr = (backend == "heap") ? static_cast<ReadyQueue*>(&hq) : static_cast<ReadyQueue*>(&aq);

    if (policy == "FCFS") res = run_fcfs(processes, *q_ptr);
    else if (policy == "SJF") res = run_sjf(processes, *q_ptr);
    else if (policy == "SRTF") res = run_srtf(processes, *q_ptr);
    else if (policy == "PRIORITY") res = run_priority(processes, *q_ptr);
    else if (policy == "RR") res = run_round_robin(processes, quantum);
    else {
        std::cerr << "Error: Unknown policy: " << policy << "\n";
        return 2;
    }

    int switches = count_context_switches(res.gantt);

    // Print JSON output
    std::cout << "{\"policy\":\"" << policy << "\",\"backend\":\"" << backend << "\",\"gantt\":[";
    for (std::size_t i = 0; i < res.gantt.size(); ++i) {
        if (i > 0) std::cout << ",";
        std::cout << "{\"pid\":" << res.gantt[i].pid << ",\"start\":" << res.gantt[i].start << ",\"end\":" << res.gantt[i].end << "}";
    }
    std::cout << "],\"metrics\":[";
    for (std::size_t i = 0; i < res.metrics.size(); ++i) {
        if (i > 0) std::cout << ",";
        std::cout << "{\"pid\":" << res.metrics[i].pid << ",\"completion\":" << res.metrics[i].completion
                  << ",\"turnaround\":" << res.metrics[i].turnaround << ",\"waiting\":" << res.metrics[i].waiting
                  << ",\"response\":" << res.metrics[i].response << "}";
    }
    std::cout << "],\"avg_waiting\":" << std::fixed << std::setprecision(6) << res.avg_waiting
              << ",\"avg_turnaround\":" << res.avg_turnaround
              << ",\"avg_response\":" << res.avg_response
              << ",\"context_switches\":" << switches << "}\n";

    return 0;
}

int main(int argc, char* argv[]) {
    try {
        if (argc >= 3 && std::string_view(argv[1]) == "--batch") {
            return run_batch(argv[2]);
        }

        DynArray<Process> processes;
        BST<PidIndex> bst_index;
        Stack<ContextSwitch> cs_history;

        std::cout << "VerifiedDS Simulator CLI\n";

        while (true) {
            std::cout << "\nMenu:\n"
                      << "1. Add process\n"
                      << "2. Delete process by PID\n"
                      << "3. Update process\n"
                      << "4. Search process by PID\n"
                      << "5. Display processes (PID order)\n"
                      << "6. Sort processes\n"
                      << "7. Run policy\n"
                      << "8. View context-switch history\n"
                      << "9. Exit\n"
                      << "Choice: ";

            int choice = 0;
            if (!(std::cin >> choice)) {
                if (std::cin.eof()) {
                    std::cout << "\nEOF detected. Exiting.\n";
                    return 0;
                }
                std::cout << "Invalid input. Please enter a number.\n";
                std::cin.clear();
                std::string dummy;
                std::cin >> dummy;
                continue;
            }

            if (choice == 1) {
                int pid = 0, arrival = 0, burst = 0, priority = 0;
                std::cout << "Enter PID, Arrival, Burst, Priority: ";
                if (!(std::cin >> pid >> arrival >> burst >> priority)) {
                    std::cout << "Invalid input.\n";
                    std::cin.clear();
                    std::string dummy;
                    std::cin >> dummy;
                    continue;
                }
                try {
                    DynArray<Process> temp = processes;
                    temp.push_back(Process{pid, arrival, burst, priority});
                    validate_processes(temp);
                    processes = temp;
                    rebuild_bst(processes, bst_index);
                    std::cout << "Process added successfully.\n";
                } catch (const std::exception& err) {
                    std::cout << "Error adding process: " << err.what() << "\n";
                }
            } else if (choice == 2) {
                int pid = 0;
                std::cout << "Enter PID to delete: ";
                if (!(std::cin >> pid)) {
                    std::cout << "Invalid PID.\n";
                    std::cin.clear();
                    std::string dummy;
                    std::cin >> dummy;
                    continue;
                }
                if (bst_index.search(PidIndex{pid, 0})) {
                    DynArray<Process> updated;
                    for (std::size_t i = 0; i < processes.size(); ++i) {
                        if (processes[i].pid != pid) {
                            updated.push_back(processes[i]);
                        }
                    }
                    processes = updated;
                    rebuild_bst(processes, bst_index);
                    std::cout << "Process " << pid << " deleted.\n";
                } else {
                    std::cout << "PID " << pid << " not found.\n";
                }
            } else if (choice == 3) {
                int pid = 0;
                std::cout << "Enter PID to update: ";
                if (!(std::cin >> pid)) {
                    std::cout << "Invalid PID.\n";
                    std::cin.clear();
                    std::string dummy;
                    std::cin >> dummy;
                    continue;
                }
                std::size_t found_idx = processes.size();
                for (std::size_t i = 0; i < processes.size(); ++i) {
                    if (processes[i].pid == pid) {
                        found_idx = i;
                        break;
                    }
                }
                if (found_idx == processes.size()) {
                    std::cout << "PID " << pid << " not found.\n";
                    continue;
                }
                int arr = 0, burst = 0, prio = 0;
                std::cout << "Enter new Arrival, Burst, Priority: ";
                if (!(std::cin >> arr >> burst >> prio)) {
                    std::cout << "Invalid input.\n";
                    std::cin.clear();
                    std::string dummy;
                    std::cin >> dummy;
                    continue;
                }
                try {
                    DynArray<Process> temp = processes;
                    temp[found_idx] = Process{pid, arr, burst, prio};
                    validate_processes(temp);
                    processes = temp;
                    rebuild_bst(processes, bst_index);
                    std::cout << "Process updated.\n";
                } catch (const std::exception& err) {
                    std::cout << "Error updating process: " << err.what() << "\n";
                }
            } else if (choice == 4) {
                int pid = 0;
                std::cout << "Enter PID to search: ";
                if (!(std::cin >> pid)) {
                    std::cout << "Invalid PID.\n";
                    std::cin.clear();
                    std::string dummy;
                    std::cin >> dummy;
                    continue;
                }
                if (bst_index.search(PidIndex{pid, 0})) {
                    for (std::size_t i = 0; i < processes.size(); ++i) {
                        if (processes[i].pid == pid) {
                            std::cout << "Found: PID=" << processes[i].pid << " Arrival=" << processes[i].arrival
                                      << " Burst=" << processes[i].burst << " Priority=" << processes[i].priority << "\n";
                            break;
                        }
                    }
                } else {
                    std::cout << "PID " << pid << " not found.\n";
                }
            } else if (choice == 5) {
                DynArray<PidIndex> ordered = bst_index.in_order();
                std::cout << "\nProcesses (PID order):\n";
                for (std::size_t i = 0; i < ordered.size(); ++i) {
                    std::size_t idx = ordered[i].index;
                    std::cout << "PID=" << processes[idx].pid << " Arrival=" << processes[idx].arrival
                              << " Burst=" << processes[idx].burst << " Priority=" << processes[idx].priority << "\n";
                }
            } else if (choice == 6) {
                int criterion = 0;
                std::cout << "Sort by: 1. Arrival, 2. Burst, 3. Priority: ";
                if (!(std::cin >> criterion) || criterion < 1 || criterion > 3) {
                    std::cout << "Invalid sorting choice.\n";
                    std::cin.clear();
                    std::string dummy;
                    std::cin >> dummy;
                    continue;
                }
                if (criterion == 1) {
                    stable_sort(processes, [](const Process& a, const Process& b) { return a.arrival < b.arrival; });
                } else if (criterion == 2) {
                    stable_sort(processes, [](const Process& a, const Process& b) { return a.burst < b.burst; });
                } else {
                    stable_sort(processes, [](const Process& a, const Process& b) { return a.priority < b.priority; });
                }
                rebuild_bst(processes, bst_index);
                std::cout << "Processes sorted.\n";
            } else if (choice == 7) {
                if (processes.empty()) {
                    std::cout << "No processes to run.\n";
                    continue;
                }
                int pol_choice = 0, backend_choice = 0, quantum = 3;
                std::cout << "Policy: 1. FCFS, 2. SJF, 3. SRTF, 4. RR, 5. PRIORITY: ";
                if (!(std::cin >> pol_choice) || pol_choice < 1 || pol_choice > 5) {
                    std::cout << "Invalid policy.\n";
                    continue;
                }
                if (pol_choice == 4) {
                    std::cout << "Quantum: ";
                    if (!(std::cin >> quantum) || quantum <= 0) {
                        std::cout << "Invalid quantum.\n";
                        continue;
                    }
                }
                std::cout << "Backend: 1. Array, 2. Heap: ";
                if (!(std::cin >> backend_choice) || (backend_choice != 1 && backend_choice != 2)) {
                    std::cout << "Invalid backend.\n";
                    continue;
                }

                ArrayReadyQueue aq;
                HeapReadyQueue hq;
                ReadyQueue* q_ptr = (backend_choice == 2) ? static_cast<ReadyQueue*>(&hq) : static_cast<ReadyQueue*>(&aq);

                ScheduleResult res;
                if (pol_choice == 1) res = run_fcfs(processes, *q_ptr);
                else if (pol_choice == 2) res = run_sjf(processes, *q_ptr);
                else if (pol_choice == 3) res = run_srtf(processes, *q_ptr);
                else if (pol_choice == 4) res = run_round_robin(processes, quantum);
                else res = run_priority(processes, *q_ptr);

                cs_history = extract_context_switches(res.gantt);

                std::cout << "\nGantt Chart:\n";
                for (std::size_t i = 0; i < res.gantt.size(); ++i) {
                    if (res.gantt[i].pid == -1) {
                        std::cout << "IDLE[" << res.gantt[i].start << "-" << res.gantt[i].end << "] ";
                    } else {
                        std::cout << "P" << res.gantt[i].pid << "[" << res.gantt[i].start << "-" << res.gantt[i].end << "] ";
                    }
                }
                std::cout << "\n\nPer-Process Metrics:\n";
                for (std::size_t i = 0; i < res.metrics.size(); ++i) {
                    std::cout << "P" << res.metrics[i].pid << "(comp=" << res.metrics[i].completion
                              << ", wait=" << res.metrics[i].waiting << ", tat=" << res.metrics[i].turnaround
                              << ", resp=" << res.metrics[i].response << ")\n";
                }
                std::cout << "Averages: wait=" << res.avg_waiting << " tat=" << res.avg_turnaround << " resp=" << res.avg_response << "\n";
            } else if (choice == 8) {
                std::cout << "\nContext-Switch History (most recent first):\n";
                Stack<ContextSwitch> temp;
                while (!cs_history.empty()) {
                    ContextSwitch cs = cs_history.peek();
                    cs_history.pop();
                    std::cout << "At time " << cs.time << ": P" << cs.from_pid << " -> P" << cs.to_pid << "\n";
                    temp.push(cs);
                }
                while (!temp.empty()) {
                    cs_history.push(temp.peek());
                    temp.pop();
                }
            } else if (choice == 9) {
                std::cout << "Exiting CLI.\n";
                break;
            } else {
                std::cout << "Invalid choice.\n";
            }
        }

        return 0;
    } catch (const std::exception& err) {
        std::cerr << "Unhandled exception: " << err.what() << '\n';
        return 1;
    }
}
