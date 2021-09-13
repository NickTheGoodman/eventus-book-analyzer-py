# eventus-book-analyzer-py

## Project Structure
- book-analyzer.sh
    - The bash wrapper script that serves as the entrypoint for the application.
    - Passes CLA and stdin onto book-analyzer.py.
- Book Analyzer (book-analyzer.py)
    - The Book Analyzer parses the stream of records from the limit order book from stdin.
- Bids Analyzer
    - The Bids Analyzer sees the bids in the book and recalculates the selling income (if needed).
- Asks Analyzer 
    - The Asks Analyzer sees the asks in the book and recalculates the buying expense (if needed).

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
- Day 6 [~2 hours]
    - Add testing and cleanup the repo's Dockerization