#include "Process.hpp"
#include "ReadyQueue.hpp"
#include "Scheduler.hpp"

#include <algorithm>
#include <cmath>
#undef NDEBUG
#include <cassert>
#include <iostream>
#include <random>

static bool approx_equal(double a, double b, double eps = 0.005) {
    return std::abs(a - b) <= eps;
}

void test_validation() {
    // burst <= 0 rejected
    try {
        Process p{1, 0, 0, 1};
        validate_processes(DynArray<Process>{p});
        assert(false);
    } catch (const std::invalid_argument&) {}

    // arrival < 0 rejected
    try {
        Process p{1, -1, 5, 1};
        validate_processes(DynArray<Process>{p});
        assert(false);
    } catch (const std::invalid_argument&) {}

    // duplicate pid rejected
    try {
        DynArray<Process> procs;
        procs.push_back(Process{1, 0, 5, 1});
        procs.push_back(Process{1, 2, 3, 1});
        validate_processes(procs);
        assert(false);
    } catch (const std::invalid_argument&) {}
}

void test_golden_set_a() {
    // Set A (pid, arrival, burst, priority) = (1,0,8,3) (2,1,4,1) (3,2,9,4) (4,3,5,2)
    DynArray<Process> procs;
    procs.push_back(Process{1, 0, 8, 3});
    procs.push_back(Process{2, 1, 4, 1});
    procs.push_back(Process{3, 2, 9, 4});
    procs.push_back(Process{4, 3, 5, 2});

    // FCFS: P1[0-8] P2[8-12] P3[12-21] P4[21-26]; P1(8,0,8,0) P2(12,7,11,7) P3(21,10,19,10) P4(26,18,23,18)
    {
        ArrayReadyQueue aq;
        ScheduleResult r_arr = run_fcfs(procs, aq);
        HeapReadyQueue hq;
        ScheduleResult r_heap = run_fcfs(procs, hq);
        assert(r_arr == r_heap);
        assert(approx_equal(r_arr.avg_waiting, 8.75));
        assert(approx_equal(r_arr.avg_turnaround, 15.25));
        assert(approx_equal(r_arr.avg_response, 8.75));
        assert(r_arr.metrics[0].completion == 8 && r_arr.metrics[0].waiting == 0 && r_arr.metrics[0].turnaround == 8 && r_arr.metrics[0].response == 0);
        assert(r_arr.metrics[1].completion == 12 && r_arr.metrics[1].waiting == 7 && r_arr.metrics[1].turnaround == 11 && r_arr.metrics[1].response == 7);
        assert(r_arr.metrics[2].completion == 21 && r_arr.metrics[2].waiting == 10 && r_arr.metrics[2].turnaround == 19 && r_arr.metrics[2].response == 10);
        assert(r_arr.metrics[3].completion == 26 && r_arr.metrics[3].waiting == 18 && r_arr.metrics[3].turnaround == 23 && r_arr.metrics[3].response == 18);
    }

    // SJF: P1[0-8] P2[8-12] P4[12-17] P3[17-26]; P1(8,0,8,0) P2(12,7,11,7) P3(26,15,24,15) P4(17,9,14,9)
    {
        ArrayReadyQueue aq;
        ScheduleResult r_arr = run_sjf(procs, aq);
        HeapReadyQueue hq;
        ScheduleResult r_heap = run_sjf(procs, hq);
        assert(r_arr == r_heap);
        assert(approx_equal(r_arr.avg_waiting, 7.75));
        assert(approx_equal(r_arr.avg_turnaround, 14.25));
        assert(approx_equal(r_arr.avg_response, 7.75));
        assert(r_arr.metrics[0].completion == 8 && r_arr.metrics[0].waiting == 0);
        assert(r_arr.metrics[1].completion == 12 && r_arr.metrics[1].waiting == 7);
        assert(r_arr.metrics[2].completion == 26 && r_arr.metrics[2].waiting == 15);
        assert(r_arr.metrics[3].completion == 17 && r_arr.metrics[3].waiting == 9);
    }

    // SRTF: P1[0-1] P2[1-5] P4[5-10] P1[10-17] P3[17-26]; P1(17,9,17,0) P2(5,0,4,0) P3(26,15,24,15) P4(10,2,7,2)
    {
        ArrayReadyQueue aq;
        ScheduleResult r_arr = run_srtf(procs, aq);
        HeapReadyQueue hq;
        ScheduleResult r_heap = run_srtf(procs, hq);
        assert(r_arr == r_heap);
        assert(approx_equal(r_arr.avg_waiting, 6.5));
        assert(approx_equal(r_arr.avg_turnaround, 13.0));
        assert(approx_equal(r_arr.avg_response, 4.25));
        assert(r_arr.metrics[0].completion == 17 && r_arr.metrics[0].waiting == 9 && r_arr.metrics[0].response == 0);
        assert(r_arr.metrics[1].completion == 5 && r_arr.metrics[1].waiting == 0 && r_arr.metrics[1].response == 0);
        assert(r_arr.metrics[2].completion == 26 && r_arr.metrics[2].waiting == 15 && r_arr.metrics[2].response == 15);
        assert(r_arr.metrics[3].completion == 10 && r_arr.metrics[3].waiting == 2 && r_arr.metrics[3].response == 2);
    }

    // RR q=3: P1[0-3] P2[3-6] P3[6-9] P4[9-12] P1[12-15] P2[15-16] P3[16-19] P4[19-21] P1[21-23] P3[23-26]
    {
        ScheduleResult r_rr = run_round_robin(procs, 3);
        assert(approx_equal(r_rr.avg_waiting, 13.5));
        assert(approx_equal(r_rr.avg_turnaround, 20.0));
        assert(approx_equal(r_rr.avg_response, 3.0));
        assert(r_rr.metrics[0].completion == 23 && r_rr.metrics[0].waiting == 15 && r_rr.metrics[0].response == 0);
        assert(r_rr.metrics[1].completion == 16 && r_rr.metrics[1].waiting == 11 && r_rr.metrics[1].response == 2);
        assert(r_rr.metrics[2].completion == 26 && r_rr.metrics[2].waiting == 15 && r_rr.metrics[2].response == 4);
        assert(r_rr.metrics[3].completion == 21 && r_rr.metrics[3].waiting == 13 && r_rr.metrics[3].response == 6);
    }

    // PRIORITY: same Gantt and values as SJF
    {
        ArrayReadyQueue aq;
        ScheduleResult r_arr = run_priority(procs, aq);
        HeapReadyQueue hq;
        ScheduleResult r_heap = run_priority(procs, hq);
        assert(r_arr == r_heap);
        assert(approx_equal(r_arr.avg_waiting, 7.75));
        assert(approx_equal(r_arr.avg_turnaround, 14.25));
        assert(approx_equal(r_arr.avg_response, 7.75));
    }
}

void test_golden_set_b() {
    // Set B = (1,2,3,1) (2,10,2,2) (3,11,4,1)
    DynArray<Process> procs;
    procs.push_back(Process{1, 2, 3, 1});
    procs.push_back(Process{2, 10, 2, 2});
    procs.push_back(Process{3, 11, 4, 1});

    ArrayReadyQueue aq;
    HeapReadyQueue hq;

    ScheduleResult r_fcfs = run_fcfs(procs, aq);
    ScheduleResult r_sjf = run_sjf(procs, hq);
    ScheduleResult r_srtf = run_srtf(procs, aq);
    ScheduleResult r_prio = run_priority(procs, hq);
    ScheduleResult r_rr = run_round_robin(procs, 2);

    assert(r_fcfs == r_sjf);
    assert(r_fcfs == r_srtf);
    assert(r_fcfs == r_prio);
    assert(r_fcfs == r_rr);

    assert(approx_equal(r_fcfs.avg_waiting, 0.333333, 0.005));
    assert(approx_equal(r_fcfs.avg_turnaround, 3.333333, 0.005));
    assert(approx_equal(r_fcfs.avg_response, 0.333333, 0.005));

    // Check Gantt has IDLE[0-2] P1[2-5] IDLE[5-10] P2[10-12] P3[12-16]
    assert(r_fcfs.gantt.size() == 5);
    assert(r_fcfs.gantt[0].pid == -1 && r_fcfs.gantt[0].start == 0 && r_fcfs.gantt[0].end == 2);
    assert(r_fcfs.gantt[1].pid == 1 && r_fcfs.gantt[1].start == 2 && r_fcfs.gantt[1].end == 5);
    assert(r_fcfs.gantt[2].pid == -1 && r_fcfs.gantt[2].start == 5 && r_fcfs.gantt[2].end == 10);
    assert(r_fcfs.gantt[3].pid == 2 && r_fcfs.gantt[3].start == 10 && r_fcfs.gantt[3].end == 12);
    assert(r_fcfs.gantt[4].pid == 3 && r_fcfs.gantt[4].start == 12 && r_fcfs.gantt[4].end == 16);
}

void verify_invariants(const DynArray<Process>& procs, const ScheduleResult& res) {
    // Slices sorted and non-overlapping
    int total_burst = 0;
    for (std::size_t i = 0; i < procs.size(); ++i) {
        total_burst += procs[i].burst;
    }

    int busy_time = 0;
    for (std::size_t i = 0; i < res.gantt.size(); ++i) {
        assert(res.gantt[i].start < res.gantt[i].end);
        if (i > 0) {
            assert(res.gantt[i].start == res.gantt[i - 1].end);
        }
        if (res.gantt[i].pid != -1) {
            busy_time += (res.gantt[i].end - res.gantt[i].start);
        }
    }
    assert(busy_time == total_burst);

    // Metric identities
    for (std::size_t i = 0; i < res.metrics.size(); ++i) {
        const auto& m = res.metrics[i];
        // find matching process
        int arr_time = -1;
        int burst_time = -1;
        for (std::size_t j = 0; j < procs.size(); ++j) {
            if (procs[j].pid == m.pid) {
                arr_time = procs[j].arrival;
                burst_time = procs[j].burst;
                break;
            }
        }
        assert(m.turnaround == m.completion - arr_time);
        assert(m.waiting == m.turnaround - burst_time);
        assert(m.response >= 0 && m.response <= m.waiting);
    }
}

void test_random_workloads() {
    std::mt19937 rng(12345);
    std::uniform_int_distribution<int> num_procs_dist(1, 30);
    std::uniform_int_distribution<int> arrival_dist(0, 50);
    std::uniform_int_distribution<int> burst_dist(1, 20);
    std::uniform_int_distribution<int> prio_dist(1, 5);

    ArrayReadyQueue aq;
    HeapReadyQueue hq;

    for (int seed = 0; seed < 1000; ++seed) {
        int n = num_procs_dist(rng);
        DynArray<Process> procs;
        for (int p = 1; p <= n; ++p) {
            procs.push_back(Process{p, arrival_dist(rng), burst_dist(rng), prio_dist(rng)});
        }

        // FCFS
        ScheduleResult r_fcfs_arr = run_fcfs(procs, aq);
        ScheduleResult r_fcfs_heap = run_fcfs(procs, hq);
        assert(r_fcfs_arr == r_fcfs_heap);
        verify_invariants(procs, r_fcfs_arr);

        // SJF
        ScheduleResult r_sjf_arr = run_sjf(procs, aq);
        ScheduleResult r_sjf_heap = run_sjf(procs, hq);
        assert(r_sjf_arr == r_sjf_heap);
        verify_invariants(procs, r_sjf_arr);

        // SRTF
        ScheduleResult r_srtf_arr = run_srtf(procs, aq);
        ScheduleResult r_srtf_heap = run_srtf(procs, hq);
        assert(r_srtf_arr == r_srtf_heap);
        verify_invariants(procs, r_srtf_arr);

        // PRIORITY
        ScheduleResult r_prio_arr = run_priority(procs, aq);
        ScheduleResult r_prio_heap = run_priority(procs, hq);
        assert(r_prio_arr == r_prio_heap);
        verify_invariants(procs, r_prio_arr);

        // RR
        ScheduleResult r_rr = run_round_robin(procs, 4);
        verify_invariants(procs, r_rr);
    }
}

int main() {
    try {
        test_validation();
        test_golden_set_a();
        test_golden_set_b();
        test_random_workloads();
        std::cout << "All S-02 scheduler tests passed successfully!\n";
        return 0;
    } catch (const std::exception& err) {
        std::cerr << "Unhandled exception: " << err.what() << '\n';
        return 1;
    }
}
