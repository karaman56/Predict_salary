import requests
import os
from dotenv import load_dotenv
from collections import defaultdict
from terminaltables import AsciiTable


def get_api_key():
    load_dotenv()
    api_key = os.getenv('API_KEY')
    return api_key

def get_languages():
    return [
        "Python",
        "Java",
        "JavaScript",
        "C#",
        "C++",
        "Ruby",
        "PHP",
        "Swift",
        "Go",
        "Kotlin"
    ]

def predict_rub_salary(vacancy):
    salary = vacancy.get('salary')
    if salary is None:
        return None

    currency = salary.get('currency')
    if currency != 'RUR':
        return None

    salary_from = salary.get('from')
    salary_to = salary.get('to')

    if salary_from is not None and salary_to is not None:
        return (salary_from + salary_to) / 2
    elif salary_from is not None:
        return salary_from * 1.2
    elif salary_to is not None:
        return salary_to * 0.8
    else:
        return None

def get_hh_statistics(languages):
    salary_statistics = {}
    for language in languages:
        vacancies_found = 0
        vacancies_processed = 0
        total_salary = 0
        page = 0
        while True:
            params = {
                "text": language,
                "area": 1,
                "per_page": 100,
                "page": page
            }
            response = requests.get("https://api.hh.ru/vacancies", params=params)
            data = response.json()
            if page == 0:
                vacancies_found = data.get('found', 0)
            if 'items' not in data or not data['items']:
                break
            for item in data['items']:
                expected_salary = predict_rub_salary(item)
                if expected_salary is not None:
                    total_salary += expected_salary
                    vacancies_processed += 1
            page += 1
        average_salary = int(total_salary / vacancies_processed) if vacancies_processed > 0 else 0
        salary_statistics[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
    return salary_statistics

def search_programmer_vacancies(keyword, town_id, catalog_id, api_key):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {
        'X-Api-App-Id': api_key,
        'Content-Type': 'application/json'
    }
    vacancies = []
    page = 0
    total_vacancies_found = 0

    while True:
        params = {
            'keyword': keyword,
            'town': town_id,
            'count': 100,
            'catalogues': catalog_id,
            'page': page
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            total_vacancies_found = data.get('total', 0)
            vacancies.extend(data.get('objects', []))
            if len(data.get('objects', [])) < 100:
                break
            page += 1
        else:
            break
    return vacancies, total_vacancies_found

def predict_salary(salary_from, salary_to):
    if salary_from is not None and salary_to is not None:
        return (salary_from + salary_to) / 2
    elif salary_from is not None:
        return salary_from
    elif salary_to is not None:
        return salary_to
    else:
        return None

def predict_rub_salary_sj(vacancy):
    salary_from = vacancy.get('payment_from')
    salary_to = vacancy.get('payment_to')
    return predict_salary(salary_from, salary_to)

def get_sj_statistics(languages, api_key):
    statistics = defaultdict(lambda: {
        "vacancies_found": 0,
        "vacancies_processed": 0,
        "average_salary": 0
    })
    for language in languages:
        vacancies, total_vacancies_found = search_programmer_vacancies(language, town_id=4, catalog_id=48,
                                                                       api_key=api_key)
        for vacancy in vacancies:
            salary = predict_rub_salary_sj(vacancy)
            statistics[language]["vacancies_found"] += 1
            if salary is not None:
                statistics[language]["vacancies_processed"] += 1
                statistics[language]["average_salary"] += salary


    for profession, stats in statistics.items():
        if stats["vacancies_processed"] > 0:
            stats["average_salary"] /= stats["vacancies_processed"]

    return statistics


def print_statistics_table(statistics, title):
    table_data = [[title, "Найдено вакансий", "Обработано вакансий", "Средняя зарплата"]]

    for profession, stats in statistics.items():
        table_data.append([
            profession,
            stats["vacancies_found"],
            stats["vacancies_processed"],
            int(stats["average_salary"])
        ])
    table = AsciiTable(table_data)
    print(table.table)

def main():
    api_key = get_api_key()
    languages = get_languages()
    hh_statistics = get_hh_statistics(languages)
    sj_statistics = get_sj_statistics(languages, api_key)
    print("Статистика по HeadHunter:")
    print_statistics_table(hh_statistics, "Язык программирования")
    print("\nСтатистика по SuperJob:")
    print_statistics_table(sj_statistics, "Язык программирования")

if __name__ == "__main__":
    main()
