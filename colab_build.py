# 将此文件内容复制到 https://colab.research.google.com 运行
# 或者在 Colab 中: File → Upload notebook → 选择 build_apk.ipynb

print("""
=== 安卓APK构建指南 ===

方法1 (推荐): Google Colab 一键构建
1. 打开 https://colab.research.google.com
2. File → Upload notebook
3. 上传 build_apk.ipynb
4. Runtime → Run all
5. 等待15-20分钟, APK自动下载

方法2: 用 Replit 构建
1. 打开 https://replit.com
2. 创建新 Repl → 选 "Bash"
3. 粘贴以下命令:

pip install buildozer cython
buildozer init
# 将 buildozer.spec 和 main.py 上传到 Repl
buildozer android debug

方法3: 本地 Docker 构建
1. 安装 Docker Desktop
2. 在 android_app 目录运行:
docker run --rm -v "%cd%":/app -w /app kivy/buildozer python3 -m buildozer android debug
""")
