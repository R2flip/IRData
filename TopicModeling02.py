import pyLDAvis.lda_model
import pyLDAvis
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import pandas as pd
import jieba
import re
import os

# 待做 LDA 的文本 csv 文件，可以是本地文件，也可以是远程文件，一定要保证它是存在的！！！！
source_csv_path = 'dcard_v1_edu_04.csv'
# 待分词的 csv 文件中的列
document_column_name = 'content'
# 输出主题词的文件路径
top_words_csv_path = 'top-topic-words.csv'
# 输出各文档所属主题的文件路径
predict_topic_csv_path = 'document-distribution.csv'
# 可视化 html 文件路径
html_path = 'document-lda-visualization.html'
# 选定的主题数
n_topics = 5
# 要输出的每个主题的前 n_top_words 个主题词数
n_top_words = 15
# 去除无意义字符的正则表达式
pattern = u'[\\s\\d,.<>/?:;\'\"[\\]{}()\\|~!\t"@#$%^&*\\-_=+，。\n《》、？：；“”‘’｛｝【】（）…￥！—┄－]+'

def top_words_data_frame(model: LatentDirichletAllocation,
                         tf_idf_vectorizer: TfidfVectorizer,
                         n_top_words: int) -> pd.DataFrame:
    rows = []
    feature_names = tf_idf_vectorizer.get_feature_names_out()
    for topic in model.components_:
        top_words = [feature_names[i]
                     for i in topic.argsort()[:-n_top_words - 1:-1]]
        rows.append(top_words)
    columns = [f'topic word {i+1}' for i in range(n_top_words)]
    df = pd.DataFrame(rows, columns=columns)

    return df


def predict_to_data_frame(model: LatentDirichletAllocation, X: np.ndarray) -> pd.DataFrame:
    matrix = model.transform(X)
    columns = [f'P(topic {i+1})' for i in range(len(model.components_))]
    df = pd.DataFrame(matrix, columns=columns)
    return df


df = (
    pd.read_csv(
        source_csv_path,
        encoding='utf-8-sig')
    .drop_duplicates()
    .rename(columns={
        document_column_name: 'text'
    }))
# 设置停用词集合
stop_words_set = set(['你', '我', '的', '是', '和'])
# 去重、去缺失、分词
df['cut'] = (
    df['text']
    .apply(lambda x: str(x))
    .apply(lambda x: re.sub(pattern, ' ', x))
    .apply(lambda x: " ".join([word for word in jieba.lcut(x) if word not in stop_words_set]))
)

# 构造 tf-idf
tf_idf_vectorizer = TfidfVectorizer()
tf_idf = tf_idf_vectorizer.fit_transform(df['cut'])

lda = LatentDirichletAllocation(
    n_components=n_topics,
    max_iter=500,
    learning_method='online',
    learning_offset=500,
    random_state=0)

# 使用 tf_idf 语料训练 lda 模型
lda.fit(tf_idf)

# 计算 n_top_words 个主题词
top_words_df = top_words_data_frame(lda, tf_idf_vectorizer, n_top_words)

# 保存 n_top_words 个主题词到 csv 文件中
top_words_df.to_csv(top_words_csv_path, encoding='utf-8-sig', index=None)

# 转 tf_idf 为数组，以便后面使用它来对文本主题概率分布进行计算
X = tf_idf.toarray()

# 计算完毕主题概率分布情况
predict_df = predict_to_data_frame(lda, X)

# 保存文本主题概率分布到 csv 文件中
predict_df.to_csv(predict_topic_csv_path, encoding='utf-8-sig', index=None)

# 使用 pyLDAvis 进行可视化
data = pyLDAvis.lda_model.prepare(lda, tf_idf, tf_idf_vectorizer)
pyLDAvis.save_html(data, html_path)
# 清屏
os.system('clear')
# 浏览器打开 html 文件以查看可视化结果
os.system(f'start {html_path}')

print('本次生成了文件：',
      top_words_csv_path,
      predict_topic_csv_path,
      html_path)
