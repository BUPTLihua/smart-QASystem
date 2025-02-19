# 该代码实现了一个简单的Flask Web应用，提供了基于StrictQASystem的问答服务。
# 用户可以通过Web接口发送问题，系统会根据预先存储的文档和知识生成专业的答案。
# Flask Web应用提供了一个问答接口，并允许前端通过API与后端交互。
# 使用了CORS来允许跨域请求，支持在不同的前端和后端服务器之间的交互。
# 在`qa`接口中，前端通过POST请求向后端发送问题，后端调用问答系统并返回生成的答案。
# 该系统通过集成一个经过训练的文本生成模型，确保回答基于预定义的文档内容。

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from qa_system_pro import StrictQASystem  # 导入自定义的QA系统

# 创建Flask应用实例
app = Flask(__name__)
CORS(app)  # 启用CORS，允许跨域请求

# 初始化QA系统
API_KEY = ""  # 这里替换成你的API密钥
qa_system = StrictQASystem(api_key=API_KEY)  # 创建QA系统实例


@app.route('/')
def index():
    """主页路由，渲染首页"""
    return render_template('index.html')  # 返回主页的HTML模板


@app.route('/qa', methods=['POST'])
def qa():
    """处理问答请求"""
    try:
        # 获取前端发送的JSON数据
        data = request.json
        question = data.get('question')  # 从数据中提取问题

        if not question:
            # 如果没有问题字段，则返回错误响应
            return jsonify({'error': '问题不能为空'}), 400

        # 使用QA系统生成答案
        answer = qa_system.generate_answer(question)  # 调用自定义问答系统的生成答案方法

        # 返回答案给前端
        return jsonify({'answer': answer})

    except Exception as e:
        # 如果处理过程中发生错误，打印错误信息，并返回服务器内部错误响应
        print(f"发生错误: {str(e)}")  # 在控制台打印错误信息
        return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    # 运行Flask应用，启动Web服务
    print("启动Web服务...")
    print("请在浏览器中访问 http://localhost:5000")  # 提示用户访问的地址
    app.run(host='0.0.0.0', port=5000, debug=True)  # 监听所有IP地址，运行在5000端口，开启调试模式
