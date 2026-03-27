Complete steps to follow to download the Jarvis on your system:



1\. Download the Jarvis file



2\. Download MSVC Build Tool - link https://aka.ms/vs/17/release/vs\_BuildTools.exe
    select - Desktop development with C++



3\. Download the Python 3.13 (Note if not working downgrade the python version with Python 3.11 or 3.12) and Node JS v20.19.6:

    Python download - https://www.python.org/downloads/windows/

    Node JS download - https://nodejs.org/en/download



4\. Create Virtual environment - Python -m venv venv

    Run below mentioned command in powershell and Remember run the powershell with the administration rights

    👉🏻 Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

    Then Activate it - venv/scripts/activate

    How to select Venv Step by Step:
    - Press - CTRL + Shift + P
    - Search - Python Select Interpreter
    - Select - Enter Interpreter Path...
    - Click on Find
    - Select Backend folder "Jarvis_code"
    - Search Python there
    - Select it.

    Then Install the liberaries - pip install -r requirements.txt

5\. GUI Package:

    Create A File **.env.local** then paste the Livekit API keys here

    Open the free terminal And Enter - cd .\\agent-starter-react\\

    Run These Command

     	- npm install -g pnpm

     	- pnpm install

     	- pnpm add -D concurrently

6\. Run Jarvis - pnpm dev

Face any issue watch this video - https://youtu.be/4iHWejxS3\_s

You can also read this conversation - https://chatgpt.com/share/69317f5d-85e4-800c-980d-98083169d55e



------------------ Join The Indian AI Tech Community Now ------------------------

Visit - https://www.youtube.com/@sachdevaAI

