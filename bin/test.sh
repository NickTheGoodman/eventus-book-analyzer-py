#!/bin/bash
#
# test.sh: Execute end-to-end test cases and check the output files
TEST_DIR="test_data"

function cleanup_test_files() {
  rm -f $TEST_DIR/*.out.*
  rm -f $TEST_DIR/*.err.*
}

TEST_CASES=(
  "test_data/bid_test00.in|350"
  "test_data/bid_test00_with_errors.in|350"
  "test_data/bid_test01.in|200"
  "test_data/book_analyzer.in|1"
  "test_data/book_analyzer.in|200"
  "test_data/book_analyzer.in|10000"
)

cleanup_test_files

for test_case in ${TEST_CASES[*]}; do
  input_file=$(echo "$test_case" | cut -d'|' -f1)
  target_size=$(echo "$test_case" | cut -d'|' -f2)
  filename_without_suffix=$(echo "$input_file" | cut -d'.' -f1)
  out_file="${filename_without_suffix}.out.$target_size"
  err_file="${filename_without_suffix}.err.$target_size"
  correct_out_file="${filename_without_suffix}.correct-out.$target_size"
  correct_err_file="${filename_without_suffix}.correct-err.$target_size"

  CMD="./book_analyzer.sh $target_size < $input_file > $out_file 2>$err_file"
  echo "Command:        $CMD"
  START=$(date +%s.%N)
  eval "$CMD"
  END=$(date +%s.%N)
  ELAPSED=$(echo "$END - $START" | bc)
  echo "Execution time: $ELAPSED"

  out_diff=$(diff "$out_file" "$correct_out_file")
  out_diff_check=$(echo "$out_diff" | wc -l)
  if [ "$out_diff_check" -ge 2 ]; then
    echo "FAIL. Diff detected between stdout file and correct output file."
  fi

  err_diff=$(diff "$err_file" "$correct_err_file")
  err_diff_check=$(echo "$err_diff" | wc -l)
  if [ "$err_diff_check" -ge 2 ]; then
    echo "FAIL. Diff detected between stderr file and correct error file."
  fi
done