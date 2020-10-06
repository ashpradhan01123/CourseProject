# EducationalWeb

1. You should have ElasticSearch installed and running -- https://www.elastic.co/guide/en/elasticsearch/reference/current/targz.html

2. Create the index in ElasticSearch using create_es_index.py

3. Download tfidf_outputs.zip from here -- https://drive.google.com/file/d/19ia7CqaHnW3KKxASbnfs2clqRIgdTFiw/view?usp=sharing
   Unzip the file and place the folder under EducationalWeb/static

4. Download cs410.zip from here -- https://drive.google.com/file/d/19ia7CqaHnW3KKxASbnfs2clqRIgdTFiw/view?usp=sharing
   Unzip the file and place the folder under EducationalWeb/pdf.js/static/slides/
   
5. From EducationalWeb/pdf.js/build/generic/web, run the following command: gulp server

6. In another terminal window, run `python app.py`

