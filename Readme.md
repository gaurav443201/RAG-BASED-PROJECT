# How to use this RAG AI Teaching assistant on your own data ?


## step 1 - Collect your video
Move all the video files to the video folder 

## step 2 - Convert to mp3
convert all the video files to mp3 by running video_to_mp3

## step 3 - Convert mp3 to json
convert all the mp3 files to json by running mp3_to_json

## step 4 - Convert the json files to vectors
Use the file preprocess_json to convert the json files to a dataframe with Embedding

## step 5 - Prompt generation and feeling to LLM 
Read the joblib file and load it into the memory. Then create a prompt as per the user query and feed it to the LLM

