# 선박 출항 판단기

풍속, 파고, 시정과 선박 상태를 바탕으로 출항 여부를 3단계로 분류하는 Python 예제입니다.

## 웹 화면으로 실행

```powershell
python web_app.py
```

그런 다음 브라우저에서 `http://127.0.0.1:8000`을 여세요. 별도 패키지 설치는 필요 없습니다.

```powershell
python voyage_checker.py --wind 8 --wave 1.5 --visibility 3 --length 20
python voyage_checker.py --wind 16 --wave 2 --visibility 3 --length 20 --json
python voyage_checker.py --wind 5 --wave 1 --visibility 4 --length 20 --engine-fault
```

기본 기준은 `Limits` 클래스에서 변경할 수 있습니다. 현재 값은 교육용 예시이며 선종, 크기, 항로, 항만 및 관할 법령에 따른 실제 기준이 아닙니다. 실운항에는 관할 기관의 출항통제 기준, 최신 기상정보, 선박 검사 상태와 선장 또는 운항관리자의 판단을 적용해야 합니다.

테스트 실행:

```powershell
python -m unittest -v
```
