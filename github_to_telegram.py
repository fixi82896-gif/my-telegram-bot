name: Auto Config & Proxy Forwarder

on:
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests

    - name: Run Script
      env:
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        TELEGRAM_CHANNEL_V2RAY_ID: ${{ secrets.TELEGRAM_CHANNEL_V2RAY_ID }}
        TELEGRAM_CHANNEL_PROXY_ID: ${{ secrets.TELEGRAM_CHANNEL_PROXY_ID }}
      run: python github_to_telegram.py

    - name: Commit and Push History Changes
      run: |
        git config --global user.name "github-actions[bot]"
        git config --global user.email "github-actions[bot]@users.noreply.github.com"
        git add sent_configs_history.json || true
        git commit -m "Update sent configs history [skip ci]" || true
        git push || true
