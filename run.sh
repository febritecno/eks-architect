#!/bin/bash
# EKS Architect — Start everything with live logs
cd "$(dirname "$0")"

# Colors
CY='\033[0;36m'  # cyan
GR='\033[0;32m'  # green
YL='\033[1;33m'  # yellow
RD='\033[0;31m'  # red
PU='\033[0;35m'  # purple
DIM='\033[2m'
NC='\033[0m'     # reset

echo ""
echo -e "${CY}══════════════════════════════════════════${NC}"
echo -e "${CY}  ⚙  EKS Architect — Robot Simulation${NC}"
echo -e "${CY}  Febrian Dwi Putra${NC}"
echo -e "${CY}══════════════════════════════════════════${NC}"
echo ""

# ── 1. DeepSeek server ──────────────────────
if rapid-mlx ps 2>/dev/null | grep -q "8001"; then
  echo -e "${GR}✅ DeepSeek already running on port 8001${NC}"
else
  echo -e "${YL}🚀 Starting DeepSeek Coder V2 Lite...${NC}"
  nohup rapid-mlx serve deepseek-coder-v2-lite-16b-4bit --port 8001 \
    > /tmp/eks-deepseek.log 2>&1 &
  DEEPSEEK_PID=$!
  echo -e "   PID: $DEEPSEEK_PID | log: /tmp/eks-deepseek.log"

  echo -n "   Loading model "
  for i in $(seq 1 40); do
    sleep 2
    if grep -q "Application startup complete" /tmp/eks-deepseek.log 2>/dev/null; then
      echo -e " ${GR}ready!${NC}"
      break
    fi
    echo -n "."
  done
fi

echo ""

# ── 2. EKS API ──────────────────────────────
echo -e "${YL}🚀 Starting EKS API on port 8002...${NC}"
# run with unbuffered output so logs stream immediately
uv run python -u api.py 2>&1 | while IFS= read -r line; do
  # color-code log lines
  if echo "$line" | grep -q "ERROR\|error\|Exception\|Traceback"; then
    echo -e "${RD}  [API] $line${NC}"
  elif echo "$line" | grep -q "evolved\|PROMOTE\|Promoted\|🧬\|🔒\|Seeded"; then
    echo -e "${GR}  [EKS] $line${NC}"
  elif echo "$line" | grep -q "Issue\|⚡\|reflect\|Reflect"; then
    echo -e "${YL}  [EKS] $line${NC}"
  elif echo "$line" | grep -q "LLM\|DeepSeek\|🧠\|🤖"; then
    echo -e "${PU}  [LLM] $line${NC}"
  elif echo "$line" | grep -q "uvicorn\|INFO\|startup\|Uvicorn"; then
    echo -e "${DIM}  [srv] $line${NC}"
  else
    echo -e "  [api] $line"
  fi
done &
API_PID=$!

# wait for API ready
sleep 4
if curl -s http://127.0.0.1:8002/status > /dev/null 2>&1; then
  echo -e "${GR}✅ EKS API ready → http://127.0.0.1:8002${NC}"
else
  echo -e "${YL}⚠  EKS API still loading...${NC}"
fi

echo ""

# ── 3. Open browser ─────────────────────────
echo -e "${CY}🌐 Opening index.html...${NC}"
open index.html

echo ""
echo -e "${CY}══════════════════════════════════════════${NC}"
echo -e "  DeepSeek : port 8001"
echo -e "  EKS API  : port 8002"
echo -e "  Logs streaming below ↓"
echo -e "  Press ${RD}Ctrl+C${NC} to stop"
echo -e "${CY}══════════════════════════════════════════${NC}"
echo ""

# keep alive and show combined logs
trap "echo ''; echo -e '${YL}Stopping...${NC}'; kill $API_PID 2>/dev/null; exit 0" INT TERM
wait $API_PID
