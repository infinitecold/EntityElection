
# Entity Linking Procedure:

## Step 0. 
   The require data file `*.tab` or `*.tsv` must be sorted properly, first based on document id and then offset within the document.
   
   If the data file is not in this format, use `src/reformat_tab.sh` sort it before proceeding to step 1.

## Step 1.
   Query wikipedia.org and google.com to generate a cache for each data set:

   Use `src/buildchinese.sh` or `src/buildcmds.sh` to generate multiple query commands:

   `buildchinese.sh run_id num_of_unique_query num_subsets data_file`

   The above generates commands using `CacheGeneration.py ...`

   These commands are fed to multiple machines using `parallel`:

    `... | parallel -j 3 -S audio,language,music,voice`

   (no more than 15 machines running concurrently due to MySQL access limit)

   Merge all subsets of caches from multiple runs into a single cache file.

## Step 2.
   After the query cache file is used, use either 

   `src/fine_tuning.sh` to generate commands to search for entity linking parameters or

   `src/EntityLinking.sh` to perform linking if the optimal parameters are known.


