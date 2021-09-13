# eventus-book-analyzer-py

## Progress Tracking

- Day 1 [~8 hrs]
    - Initial review of problem and test data
    - Walk through algorithm manually (on paper)
    - Work out initial pseudo code on paper
    - Write bash script and main python script to correctly parse CLA and stdin
    - Bonus: Setup container build & execution via Docker/docker-compose and corresponding wrapper scripts 
- Day 2 [~8 hrs]
    - Work out pseudo code on paper for a better-optimized algorithm
- Day 3 [~4 hrs]
    - Setup initial classes and market log processing
- Day 4 [~8 hrs]
    - Cleanup market log processing
    - Implement initial BidBook()
    - Introduce typing to existing classes
- Day 5 [~10 hrs]
    - Finish initial full implementation
- Day 6 [~8 hours]
    - Add testing and cleanup the repo's Dockerization
    - Fill out the rest of this README
    - Final cleanup

## Notes on Source Files and Bin Scripts
- book-analyzer.sh
    - The bash wrapper script that serves as the entrypoint for the application.
    - Passes CLA and stdin onto book-analyzer.py.
- BookAnalyzer
    - Effectively serves as the main program/class
    - Parses the stream of ADD and REDUCE commands of the market log from stdin and updates each LimitOrderBook instance
- MarketLogCommand
    - This class and its 2 child classes store info related to the input commands
- LimitOrderBook
    - Each instance of a LimitOrderBook contains all info related to either bids or asks
    - "total_price_of_taken_orders" refers to "selling income" in the bid book and "buying expense" in the ask book
- test_data/
    - The files named as "*.correct-out.###" correspond to the sample output files originally provided in the .zip.
- bin/test.sh
    - Invokes book_analyzer.sh on a few combinations of input files and target sizes. 
    - For each test case, prints the elapsed time and checks the contents of stdout and stderr against 
      the pre-determined correct results.
- bin/dc-*.sh
    - Wrapper scripts for some docker-compose commands to conveniently build and run a containerized instance of 
      book-analyzer.sh
  
## Running book_analyzer.sh

### Installation requirements

- Linux utils:
    - bash, bc 
- python3
- Docker (optional)

### On the shell (no Docker)

From the top-level dir of the repo, run:
```bash
$ ./book_analyzer.sh [target_size] < test_data/[input_file] 
```
or, to dump stdout/stderr into individual files:
```bash
$ ./book_analyzer.sh [target_size] < test_data/[input_file] > test_data/[output_file] 2> test_data/[err_file]
```

Example:
```bash
$ ./book_analyzer.sh 200 < test_data/book_analyzer.in > test_data/book_analyzer.out.200 2>test_data/book_analyzer.err.200
```

### Automated testing
Execute a few specific end-to-end test cases via test.sh:

```bash
$ bin/test.sh
```

### Running via Docker
First, build the container.
```bash
$ bin/dc-build.sh
```

Option 1. Shell into the container and run previous commands from within the container.
```bash
$ bin/dc-shell.sh
```

Option 2. Execute test.sh in the container from the host.
```bash
$ bin/dc-run.sh
```

## Design and Implementation Analysis

_**How did you choose your implementation language?**_

I used these factors to decide:
- How I could expect this algorithm to be implemented at Eventus
- The expected implementation time given my own limitations
- How my choice of language could impact the relevant tradeoffs of
  Correctness, Clarity, Conciseness, and (Co)Efficiency

In my initial interview with Dan, I took these notes:
- C++ and Python are two primary languages used in Validus's backend
- Market data processing code (from RGM) is implemented in C++

These facts alone narrowed my choices down to Python and C++ (and initially made me lean towards C++).

I knew I could achieve **Correctness** and **Clarity** in both Python and C++,
but I had to take my own rustiness into account:
I have much more recent practice with Python, and I'm generally rusty with C++. 

In my opinion, generally speaking:
- In Python, it is easier to achieve **Conciseness** and harder to achieve **Efficiency**.
- In C++, it is easier to achieve **Efficiency** and harder to achieve **Conciseness**.

I figured that if I were to consider **Conciseness** and **Efficiency** as equally important,
and since I'd be effectively "sacrificing" one to maximize the other regardless of my choice,
then I couldn't really use these to pick one language over the other.

Ultimately, I decided that I'd personally have my best chance at achieving **Correctness** and 
**Clarity** in a **timely manner** with Python, and recognized that with this choice,
I could maximize **Conciseness** while unfortunately sacrificing **Efficiency**.

_**How did you arrive at your final implementation? Were there other approaches that you considered or tried first?**_

First, I manually stepped through the Example Input and Output on paper,
tracking relevant variables and conditions as I went.
This process led naturally to a class hierarchy, data structures, and simple, un-optimized algorithms for
adding and reducing bids (I cut asks out of this process once I realized that handling bids and asks was so similar).
Sticking to paper, I made up my own test cases, trying to break my existing algorithm (I was looking for corner cases),
and discovered the conditions under which the selling income/buying expense did not need to be recalculated when
adding or reducing a bid/ask.
At this point, I realized that grouping LimitOrders into Groups by price and
storing these Groups in a Binary Search Tree were nice ways to optimize the algorithm.

Once I had AddOrder and ReduceOrder psuedo-code fully written to handle bids, I started writing code.
See the Progress Tracking section of this README for more details.
 
My initial goal was to write the simplified solution first, and then add the optimizations later 
once I achieved Correctness.
The current solution unconditionally recalculates selling income/buying expense every time a new bid/ask is added or reduced,
meaning I stopped short of implementing the smarter version of _should_calculate and incorporating a BST, unfortunately.
See the Hypothetical Next Steps for Improvement section for details.

_**How does your implementation scale with respect to the target size and with respect to the number of orders in the book?**_

Let T = target size, N = number of orders in the book (order count).

The average time complexity of my solution w.r.t. N and T is O(N * (N + T)).

All operations of BookAnalyzer() besides the add_order() and reduce_order() methods are of constant time.
add_order() and reduce_order() scale with O(N+T).
The size of the market log is directly related to N, and for each line of the market log, 
either LimitOrderBook.add_order() or reduce_order() is called once.
Therefore, the time complexity of BookAnalyzer.analyze_market_log() is O(N) * O(N+T).

The reasons add_order() and reduce_order are O(N+T) are:
- The operations related to maintaining the LimitOrder and LimitOrderGroup dicts and sorted price list 
  scale linearly with the number of LimitOrders and unique prices that have to be maintained,
  which are directly related to N.
- The recalculation of selling income / buying expense is a simple loop through the sorted price list, but
  the break condition of this loop occurs when the sum of shares of the iterated prices (LimitOrderGroups) equals 
  the target_size.
  Thus, the larger the target_size, the more iterations in the price list loop, i.e. this scales with T.

## Hypothetical Next Steps for Improvement
- Prevent needless invocations of LimitOrderBook._calculate_total_price_of_taken_orders() by 
  adding more conditions to LimitOrder._should_calculate(). For example:
    - if:
        - a new bid is being added
        - AND the new bid's price < the price of the cheapest (last) bid taken in the previously-calculated selling income,
        - THEN the selling income does NOT need to be recalculated.
    - if:
        - a bid is being reduced
        - AND the new bid's price == the price of the cheapest (last) bid previously taken
        - AND there are still leftover shares associated with that cheapest price **even after the reduction,**
        - THEN the selling income does NOT need to be recalculated.
- Refactor LimitOrderBook to use a Binary Search Tree to store LimitOrderGroups 
    - Time complexity of the solution could be improved to O(N * (logN + T))

## Raw Notes on Time Complexity Analysis
  - T = target size
  - N = number of orders in the book (order count)
  - add_order() | O(N+T)
      - add_order() 1 | O(1) to O(N) 
          - _add_order_by_id() | O(1) to O(N)
              - dict set item - scales with # of unique order IDs AKA order count
                  - Avg case: O(1)
                  - Worst case: O(N)
          - _order_group_already_exists() | O(1) to O(N)
              - key in dict.keys() - scales with # of unique prices AKA order count
                  - Avg. case: O(1)
                  - Worst case: O(N)
    
      - add_order() 2a | O(1) to O(N)
          - _add_order_to_order_group() | O(1) to O(N)
              - dict get item | O(1) to O(N)
                  - Avg. case: O(1)
                  - Worst case: O(N)
              - list.append(elem) | O(1)
                  - Avg. case: O(1)
                  - Worst case: O(1)
    
      - add_order() 2b | O(N)
          - _add_new_order_group() | O(1) to O(N)
              - dict set item | O(1) to O(N)
          - _update_sorted_list() | O(N)
              - list append(elem) | O(1)
              - sort the ordered price list | O(N)
                  - The Python Timsort best case runtime of O(N) applies as the avg. case here, 
                    because it is being run on a list where only the last element is out-of-order.
    
      - add_order() 3 | O(T) to O(T*N)
          - update_state_of_book() | O(T) to O(T*N)
              - _calculate_total_price_of_taken_orders()
                  - loop through sorted list from beginning until target_size shares have been counted
                    - O(T)                  
                    - in each iteration:
                      - dict get item | O(1) to O(N)
  
- reduce_order() O(N+T)
    - _remove_order_if_needed() | O(N)
        - del dict key | O(1) to O(N)
            - Avg. case: O(1)
            - Worst case O(N)
        - delete item from unsorted list | O(N)
            - Avg: O(N)
            - Worst: O(N)

    - _remove_order_group_if_needed | O(N)
        - del dict key | O(1) to O(N)
        - delete item from sorted list | O(N)

    - _update_state_of_book() | O(T)
      
- References
    - https://wiki.python.org/moin/TimeComplexity
    - https://en.wikipedia.org/wiki/Timsort
    - https://stackoverflow.com/questions/2994274/efficient-way-to-maintain-a-sorted-list-of-access-counts-in-python
