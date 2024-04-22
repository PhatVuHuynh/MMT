**Can:**
  - Upload files, folder:
    + Syntax: UPLOAD <file_path>
  - Download files, folder:
    + Syntax: DOWNLOAD <file_path>: if you download a folder, the end of file_path will be '\\'
  - List all files you can download now:
    + Syntax: LIST 

**How to run:**
  1. Define TRACKER_IP and TRACKER_PORT in tracker.py and peer.py
  2. python .\tracker
  3. python .\peer <peer_ip> <peer_port> <shared_file> <downloaded_file> : <shared_file> <downloaded_file> is optional
