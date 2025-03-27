from requests import Session
from bs4 import BeautifulSoup
from os import getenv
from dotenv import load_dotenv

load_dotenv()
userAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
COOKIEKEY = "ICETSESSIONID"
etlabLink = "https://icet.etlab.in"

session = Session()
session.headers.update({"User-Agent": userAgent})

session.post(
    f"{etlabLink}/user/login",
    data={
        "LoginForm[username]": getenv("USERNAME"),
        "LoginForm[password]": getenv("PASSWORD"),
        "yt0": "",
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

surveyData = BeautifulSoup(
    session.get(f"{etlabLink}/survey/user/viewall").text, "html.parser"
).find("table", class_="section table table-bordered")
surveyList = []
for tr in surveyData.find_all("tr"):
    linkEle = tr.select("td:nth-child(7) > span")
    if not linkEle:
        continue
    if "faculty" in tr.select("td:nth-child(3)")[0].text.lower():
        lnk = etlabLink + linkEle[0].a["href"]
        facultyfd = BeautifulSoup(session.get(lnk).text, "html.parser").select(
            "#section-form"
        )
        for faculty in facultyfd:
            facultyTr = faculty.find_next("tr")
            if (
                facultyTr.select("td:nth-child(4) > div > span")[0].text.strip()
                == "Completed"
            ):
                # Already completed
                continue
            teacherId = faculty.find_next("input", {"name": "teacher_id"})
            subjectId = teacherId.find_next("input", {"name": "subject_id"}).get(
                "value"
            )
            teacherId = teacherId.get("value")
            surveyList.append(
                {
                    "link": lnk,
                    "name": facultyTr.select("td:nth-child(2)")[0].text.strip(),
                    "body": {"teacher_id": teacherId, "subject_id": subjectId},
                }
            )
    else:
        surveyList.append(
            {
                "link": etlabLink + linkEle[0].a["href"],
                "name": tr.select("td:nth-child(2)")[0].text.strip(),
            }
        )

if not surveyList:
    print("No surveys pending.")
    exit()


def surveySubmitter(SurveyLink: str):
    soup = BeautifulSoup(session.get(SurveyLink).text, "html.parser")
    surveySoup = soup.select("ul.survey")[0]
    data = {"environment": "1", "yt0": ""}
    for question in surveySoup.find_all("div", class_="answer"):
        ans = question.find("input", {"type": "radio"})
        data[ans.get("name")] = ans.get("value")
    session.post(SurveyLink, data=data)


def facultySurveySubmitter(SurveyLink: str, data: dict):
    soup = BeautifulSoup(session.post(SurveyLink, data=data).text, "html.parser")
    surveySoup = soup.select("ul.survey")[0]
    data.update({"environment": "1", "yt0": ""})
    for question in surveySoup.find_all("div", class_="answer"):
        ans = question.find("input", {"type": "radio"})
        if ans:
            data[ans.get("name")] = ans.get("value")
        else:
            ans = question.find("textarea")
            data[ans.get("name")] = "Great"
    session.post(SurveyLink, data=data)


for survey in surveyList:
    if "body" in survey:
        facultySurveySubmitter(survey["link"], survey["body"])
    else:
        surveySubmitter(survey["link"])

print(
    f"Completed {len(surveyList)} survey(s).\n"
    f"Surveys \n{'\n'.join([i['name'] for i in surveyList])}"
)
