# TikTok Selling Video Workflow Skill

闈㈠悜缇庡浗 TikTok Shop 鐨?AI 甯﹁揣瑙嗛宸ヤ綔娴併€備粨搴撴棦鑳藉垎鏋愬凡鏈?UGC 鑴氭湰锛屼篃鑳芥妸宸叉牳瀹炵殑浜у搧浜嬪疄杞垚鑴氭湰銆佸瓧骞曘€佸垎闀溿€丼eedance/Sora Prompt 鍜岃川閲忔姤鍛娿€?
## MVP 宸ヤ綔娴?
```text
浜у搧浜嬪疄 -> 浜嬪疄璐︽湰 -> 鍒涙剰绠€鎶?-> A/B/C 鑴氭湰 -> 鑷姩璇勫垎
         -> 鍒嗛暅 -> 鐢熸垚 Prompt -> Prompt-only 娓叉煋浠诲姟 -> QA 鎶ュ憡
```

榛樿涓嶈皟鐢ㄤ粯璐硅棰?API锛屼篃涓嶄細鎶?Prompt 褰撴垚宸茬粡鐢熸垚鐨勮棰戙€備骇鍝佽韩浠姐€佹墜閮ㄣ€佹枃瀛椼€佸姩浣滃畨鍏ㄥ拰闊崇敾鍚屾淇濈暀涓烘垚鐗囧悗鐨勪汉宸ユ鏌ラ」銆?
## 蹇€熻繍琛?
```bash
python scripts/run_workflow.py examples/project_input.json --output outputs/demo --provider prompt-only
python -m unittest discover -s tests -v
```

閲嶆柊鎵ц鏃舵坊鍔?`--resume`锛岃緭鍏ュ搱甯屾湭鍙樺寲涓斾笂娆¤繍琛屽畬鎴愭椂浼氬鐢ㄧ幇鏈夌姸鎬併€?
## 鏍稿績鏂囦欢

```text
SKILL.md                          涓诲伐浣滄祦涓庡畨鍏ㄨ竟鐣?agents/openai.yaml                Skill UI 鍏冩暟鎹?references/                       鐘舵€佹満銆丳rovider 鍜?QA 濂戠害
schemas/                          杈撳叆涓庤緭鍑?JSON Schema
scripts/run_workflow.py           鏃犲閮ㄤ緷璧栫殑纭畾鎬х紪鎺掑櫒
prompts/                          鑴氭湰銆丠ook銆佸彛璇€佸悎瑙勫拰瑙嗛 Prompt
examples/project_input.json       鍙繍琛岀ず渚?tests/test_workflow.py            鍥炲綊娴嬭瘯
```

鍘熸湁鑴氭湰鍒嗘瀽 Prompt 淇濈暀涓哄伐浣滄祦涓殑涓撻」姝ラ銆傜粺涓€鐨?15 绉掓椂闂磋酱涓?`0-2 / 2-5 / 5-10 / 10-13 / 13-15`銆?