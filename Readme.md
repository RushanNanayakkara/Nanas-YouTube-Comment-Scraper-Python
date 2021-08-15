# Nana's YouTube comments scraper

## Requirements
- Python 3.9
- Chrome web-driver

## How to use
### Command Line Parameters
- Input file : 
  - Required parameter at position 1
  - Should be the path to the text file with the urls to  scrape
- Output path 
  - Optional parameter 
  - Default value: 'Out'
  - include custom parameter with arguments '-op' or '--outputPath'
- Output file name
  - Optional parameter
  - Default value : 'out'
  - include custom parameter with arguments '-of' or '--outputFileName'

### Usage examples
With only the input file   
`python YouTube_Scraper.py Input/example_in.txt`  

With input file and output path only  
`python YouTube_Scraper.py Input/example_in.txt -op Out`  

With input file, output path and output file name  
`python YouTube_Scraper.py Input/example_in.txt -op Out -of example_out`

### Input file format
With input file should be in .txt format with one url per line with no quotation marks

#### Input file example
```
https://examle.url1.com/vid1
https://examle.url2.com/vid2
https://examle.url3.com/vid3
https://examle.url4.com/vid4
https://examle.url5.com/vid5
```


### Output file example
```json
[
    {
        "title": "Title string here",
        "url": "https://youtube.url",
        "comments": [
            {
                "_Comment__owner": "Comment owner name",
                "_Comment__comment": "comment text",
                "_Comment__replies": [
                    {
                        "_Reply__owner": "reply comment owner name",
                        "_Reply__reply": "reply comment text"
                    }
                ]
            }
        ]
    }
]
```