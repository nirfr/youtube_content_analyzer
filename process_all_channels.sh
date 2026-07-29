#!/bin/bash

# Process all existing channels: scrape video metadata and download transcripts

CHANNELS_DIR="channels"

# Check if channels directory exists
if [ ! -d "$CHANNELS_DIR" ]; then
    echo "Error: channels directory not found"
    exit 1
fi

# Iterate through all channel directories
for channel_dir in "$CHANNELS_DIR"/*/; do
    if [ -d "$channel_dir" ]; then
        # Extract channel name from directory path
        channel_name=$(basename "$channel_dir")
        
        echo "=========================================="
        echo "Processing channel: $channel_name"
        echo "=========================================="
        
#        # Step 1: Scrape video metadata
#        echo "Step 1: Scraping video metadata..."
#        python scraper.py "$channel_name"
#        sleep 5
#
#        # Check if scraper succeeded
#        if [ $? -ne 0 ]; then
#            echo "Warning: Scraper failed for $channel_name, skipping download"
#            continue
#        fi
        
        # Step 2: Download transcripts
        echo "Step 2: Downloading transcripts..."
        python downloader.py "$channel_name"
        sleep 5
        
        if [ $? -eq 0 ]; then
            echo "Successfully processed $channel_name"
        else
            echo "Warning: Downloader encountered issues for $channel_name"
        fi
        
        echo ""
    fi
done

echo "=========================================="
echo "All channels processed"
echo "=========================================="
