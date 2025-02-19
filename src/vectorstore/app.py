from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from qa_system_pro import StrictQASystem  # 导入你的QA系统

app = Flask(__name__)
CORS(app)

# 初始化QA系统
API_KEY = "sk-TkFjGCG1NdXESZKa39D709663a7742Ba9e35359c63145039"  # 这里替换成你的API密钥
qa_system = StrictQASystem(api_key=API_KEY)


@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')


@app.route('/qa', methods=['POST'])
def qa():
    """处理问答请求"""
    try:
        data = request.json
        question = data.get('question')
        if not question:
            return jsonify({'error': '问题不能为空'}), 400

        # 使用QA系统生成答案
        answer = qa_system.generate_answer(question)
        return jsonify({'answer': answer})

    except Exception as e:
        print(f"发生错误: {str(e)}")  # 在控制台打印错误信息
        return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    print("启动Web服务...")
    print("请在浏览器中访问 http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)