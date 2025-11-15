 set   FSCRAWLER_VERSION="2.10-SNAPSHOT"
 set    FSCRAWLER_PORT="8080"
 set    DOCS_FOLDER="C:\install\Pdfs\try1"
 set    FSCRAWLER_CONFIG="c:\install\tails\fsjobs"
 set    FS_JAVA_OPTS="-DLOG_LEVEL=debug -DDOC_LEVEL=debug"
 set    COMPOSE_PROJECT_NAME=phd
docker run -d --name fs   --env FS_JAVA_OPTS=%FS_JAVA_OPTS%   -v %DOCS_FOLDER%:/tmp/es:ro   -v %FSCRAWLER_CONFIG%:/root/.fscrawler   -p %FSCRAWLER_PORT%:8080    dadoonet/fscrawler:%FSCRAWLER_VERSION%   "phd --loop 1"