# CourseProject
Please install the Educational Web as mentioned below from the CS410 Repository and then overwrite the two python scripts (app.py and model.py) from our project repository. The git push from the original repo was showing an error when we were trying to bring in the entire code. We have tested the code using Python 3.6. 

 EducationalWeb Installation Steps

The following instructions have been tested with Python2.7 on Linux and MacOS
1. Download EducationalWeb code from https://github.com/CS410Fall2020/EducationalWeb

2. You should have ElasticSearch installed and running -- https://www.elastic.co/guide/en/elasticsearch/reference/current/targz.html

3. Create the index in ElasticSearch by running `python create_es_index.py` from `EducationalWeb/`

4. Download tfidf_outputs.zip from here -- https://drive.google.com/file/d/19ia7CqaHnW3KKxASbnfs2clqRIgdTFiw/view?usp=sharing
   
  Unzip the file and place the folder under `EducationalWeb/static`

5. Download cs410.zip from here -- https://drive.google.com/file/d/1Xiw9oSavOOeJsy_SIiIxPf4aqsuyuuh6/view?usp=sharing
   
   Unzip the file and place the folder under `EducationalWeb/pdf.js/static/slides/`
   
6. From `EducationalWeb/pdf.js/build/generic/web` , run the following command: `gulp server`

7. Please install the libraries mentioned in app.py before you run the code. 
 

8. In another terminal window, run `python app.py` from `EducationalWeb/`

9. The site should be available at http://localhost:8096/

