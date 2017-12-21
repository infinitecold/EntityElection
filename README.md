
# EntityElection Entity Linking Procedure

## (Step 0: Preparation)
   The required data file `*.tab` or `*.tsv` must be sorted properly, first based on document ID and then based on entity offset within the document.
   
   If the data file is not in this format, use `src/reformat_tab.sh` to sort it before proceeding to step 1.

## Step 1: Cache Generation
   To query [Wikipedia](https://www.wikipedia.org) and [Google](https://www.google.com) to generate the cache for each data set, use `src/build_cmds.sh` or `src/build_zh_cmds.sh` (if Chinese data set) to generate multiple query commands:

   `build_cmds.sh run_id num_of_unique_query num_subsets data_file`

   The above generates commands using `CacheGeneration.py ...`. These commands are fed to multiple machines using `parallel`:

    `... | parallel -j 3 -S audio,language,music,voice`

   (NOTE: there are no more than 15 machines running concurrently due to the MySQL access limit)

   Then merge all cache subsets from parallel runs into a single cache file.

## Step 2: Linking
   After the query cache file is created, use either

   * `src/fine_tuning.sh` to generate commands to tune for optimal entity linking parameters, or

   * `src/entity_linking.sh` to perform linking if the optimal parameters are known.
