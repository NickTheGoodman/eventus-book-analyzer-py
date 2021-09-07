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

Note: each "day" is roughly 8 hours 

- Day 1
    - Initial review of problem and test data
    - Walk through algorithm manually (on paper)
    - Work out initial pseudo code on paper
    - Write bash script and main python script to correctly parse CLA and stdin
    - Bonus: Setup container build & execution via Docker/docker-compose and corresponding wrapper scripts 
- Day 2
    - Work out pseudo code on paper for a better-optimized algorithm 