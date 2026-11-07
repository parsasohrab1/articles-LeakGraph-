"""Article and achievement card for the product basket.

The measured rows are formatted from the BattLeDIM block of results.json.
The article row stays unsubmitted: the checked Water special issue is past
its printed deadline, and a patent attorney has not reviewed a manuscript.
"""

from __future__ import annotations

REPO = "https://github.com/parsasohrab1/articles-LeakGraph-"
BRANCH = "feat/leakgraph-realdata"
PULL = "https://github.com/parsasohrab1/articles-LeakGraph-/pull/2"
TITLE = "Residual leak alarms on the BattLeDIM L-Town simulated benchmark"


def _r3(value: float) -> str:
    return f"{float(value):.3f}"


def registration_markdown(bench: dict) -> str:
    """Filing card. `bench` is the battledim object written by run_study.py."""
    if bench.get("benchmark") != "simulated":
        raise ValueError("the registration card only accepts the simulated benchmark")
    simple = bench["hour_level_2019"]["simple_threshold"]
    conformal = bench["hour_level_2019"]["conformal"]
    simple_events = bench["events_2019"]["simple_threshold"]
    conformal_events = bench["events_2019"]["conformal"]
    cal = bench["calibration_false_alarm_rate"]
    return f"""# ثبت مقاله و دستاوردها

شناسه سبد: `nrwleak`. این برگه برای ثبت داخلی است. مقاله‌ای به ژورنال ارسال نشده است.

| قلم | ثبت |
|---|---|
| محصول | LeakGraph |
| ریپو | {REPO} |
| شاخه | `{BRANCH}` |
| پیش‌نویس بررسی | {PULL} |
| بلوغ | TRL 4 |
| نوع داده | بنچ‌مارک شبیه‌سازی‌شده (EPANET، L-Town) |
| داده | BattLeDIM، doi:{bench["doi"]}، {bench["license"]} |
| عنوان یادداشت | {TITLE} |
| متن | `article/abstract.md` |
| دروازه ژورنال | `docs/JOURNAL_FIT.md` |
| وضعیت مقاله | ارسال نشده |
| فراخوان بررسی‌شده | Water (MDPI)، ویژه «Looking into the Future of Smart Water Management by Artificial Intelligence (AI)»؛ مهلت چاپ‌شده ۳۰ سپتامبر ۲۰۲۶ |
| وکیل پتنت | متن ارسال را تأیید نکرده است. این برگه الگوریتم مکان‌یابی را شرح نمی‌دهد. |

## دستاورد اندازه‌گیری‌شده

منبع اعداد: `research/results.json`، کلید `battledim`، گردشده به سه رقم اعشار. ساعت‌های ارزیابی ۲۰۱۹: {bench["n_evaluation_hours"]}. ساعت‌های کالیبراسیون ۲۰۱۸: {bench["n_calibration_hours"]}. نشت‌های برچسب‌دار: {bench["n_leaks"]} (شروع ۲۰۱۸: {bench["n_leaks_2018"]}، شروع ۲۰۱۹: {bench["n_leaks_2019"]}). حسگر فشار: {bench["n_pressure_sensors"]}. سهم ساعت‌های داخل پنجره ظهور در ۲۰۱۹: {_r3(bench["evaluation_onset_rate"])}.

| قاعده | آستانه | دقت | بازخوانی | نرخ هشدار کاذب ۲۰۱۹ | نرخ هشدار کاذب کالیبراسیون |
|---|---|---|---|---|---|
| آستانه ساده | {_r3(bench["simple_threshold"])} | {_r3(simple["precision"])} | {_r3(simple["recall"])} | {_r3(simple["false_alarm_rate"])} | {_r3(cal["simple_threshold"])} |
| چندک کالیبره‌شده | {_r3(bench["conformal_threshold"])} | {_r3(conformal["precision"])} | {_r3(conformal["recall"])} | {_r3(conformal["false_alarm_rate"])} | {_r3(cal["conformal"])} |

هشدار در ۲۴ ساعت اول نشت‌های ۲۰۱۹: آستانه ساده {simple_events["n_detected_within_24h"]} از {simple_events["n"]}؛ قاعده کالیبره‌شده {conformal_events["n_detected_within_24h"]} از {conformal_events["n"]}. نرخ ۲۴ساعته روی نشت‌های ناگهانی برای قاعده کالیبره‌شده {_r3(conformal_events["by_type"]["abrupt"]["detected_within_24h"])} است و میانه تأخیر {_r3(conformal_events["median_delay_hours"])} ساعت. نرخ هشدار کاذب کالیبراسیون این قاعده {_r3(cal["conformal"])} است و روی ۲۰۱۹ به {_r3(conformal["false_alarm_rate"])} می‌رسد، پس هدف {_r3(bench["alpha"])} در سال ارزیابی برقرار نیست.

دستاورد ثبت‌شده مقایسه همین دو هشدار روی بنچ‌مارک شبیه‌سازی‌شده است.
"""
