# Financial Manager

A Single Page Application (SPA) for financial management built with Python 3.11+ and Streamlit, demonstrating functional programming concepts.

## Features

- **Domain Models**: Immutable data structures (Account, Category, Transaction, Budget).
- **Functional Core**: Pure functions, Higher-Order Functions, Closures.
- **Recursion**: Recursive category flattening and expense summation.
- **Memoization**: Caching expensive forecast calculations.
- **Functional Types**: `Maybe` and `Either` monads for error handling.
- **Lazy Evaluation**: Generators for efficient data processing.
- **FRP**: Event Bus for reactive updates (Transactions, Alerts).
- **Composition**: Function composition and piping.
- **Async**: Asynchronous report generation.

## Project Structure

```
project/
  app/
    main.py         # Streamlit entry point and UI logic
  core/
    domain.py       # Immutable models
    transforms.py   # Pure functions & transforms
    recursion.py    # Recursive algorithms
    memo.py         # Memoization / Caching
    ftypes.py       # Maybe / Either types
    lazy.py         # Lazy iterators
    frp.py          # Functional Reactive Programming / Event Bus
    compose.py      # Composition utilities
    service.py      # Domain services
  data/
    seed.json       # Seed data
  tests/            # Pytest suite
  README.md
  requirements.txt
```

## Setup & Running

1. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate   # Windows
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**
   ```bash
   streamlit run app/main.py
   ```

4. **Run Tests**
   ```bash
   pytest
   ```

## Labs & Implementation

- **Lab 1**: Pure functions, Immutability. (Overview Menu)
- **Lab 2**: Closures, Recursion. (Functional Core / Pipelines Menu)
- **Lab 3**: Memoization (`lru_cache`). (Reports Menu)
- **Lab 4**: Maybe/Either containers. (Pipelines Menu)
- **Lab 5**: Lazy evaluation/Generators. (Pipelines Menu)
- **Lab 6**: FRP / Event Bus. (Async/FRP Menu)
- **Lab 7**: Composition, Services. (Reports Menu)
- **Lab 8**: Async/Parallelism. (Async/FRP Menu)

## Team
- Student 1
- Student 2
- Student 3
