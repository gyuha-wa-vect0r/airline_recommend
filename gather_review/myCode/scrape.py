import requests
from bs4 import BeautifulSoup
import json
import time

# User-Agent 설정
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# A-Z 페이지에서 모든 항공사 링크 수집
def get_all_airline_links(base_url):
    response = requests.get(base_url, headers=HEADERS)
    if response.status_code != 200:
        print("A-Z 리뷰 페이지를 가져오지 못했습니다.")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    airline_links = [
        "https://www.airlinequality.com" + link["href"]
        for link in soup.select("a[href^='/airline-reviews/']")
    ]
    print(f"총 {len(airline_links)}개의 항공사 리뷰 링크를 수집하겠습니다.")
    return airline_links

# 항공사 리뷰 크롤링
def scrape_airline_reviews(airline_url, max_pages=3):
    reviews_data = []
    for page in range(1, max_pages + 1):
        print(f"  -> {airline_url.split('/')[-1]}: {page} 페이지 크롤링 시작...")
        url = f"{airline_url}/?sortby=post_date%3ADesc&pagesize=100&page={page}" if page > 1 else f"{airline_url}/?sortby=post_date%3ADesc&pagesize=100"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"    -> {airline_url} 페이지 {page}를 가져오지 못했습니다. 상태 코드: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        review_sections = soup.select("article[itemprop='review']")

        for review in review_sections:
            # 필드 추출
            overall_rating = review.select_one("span[itemprop='ratingValue']").get_text(strip=True) if review.select_one("span[itemprop='ratingValue']") else None
            title = review.select_one(".text_header").get_text(strip=True) if review.select_one(".text_header") else None
            review_date = review.select_one("meta[itemprop='datePublished']").get("content") if review.select_one("meta[itemprop='datePublished']") else None
            author = review.select_one("span[itemprop='name']").get_text(strip=True) if review.select_one("span[itemprop='name']") else None
            content = review.select_one(".text_content").get_text(strip=True) if review.select_one(".text_content") else None
            traveller_type = review.select_one(".review-rating-header.type_of_traveller + td").get_text(strip=True) if review.select_one(".review-rating-header.type_of_traveller + td") else None
            seat_type = review.select_one(".review-rating-header.cabin_flown + td").get_text(strip=True) if review.select_one(".review-rating-header.cabin_flown + td") else None
            route = review.select_one(".review-rating-header.route + td").get_text(strip=True) if review.select_one(".review-rating-header.route + td") else None
            date_flown = review.select_one(".review-rating-header.date_flown + td").get_text(strip=True) if review.select_one(".review-rating-header.date_flown + td") else None
            seat_comfort = len(review.select(".review-rating-header.seat_comfort + td .star.fill"))
            cabin_service = len(review.select(".review-rating-header.cabin_staff_service + td .star.fill"))
            food_beverages = len(review.select(".review-rating-header.food_and_beverages + td .star.fill"))
            inflight_entertainment = len(review.select(".review-rating-header.inflight_entertainment + td .star.fill"))
            ground_service = len(review.select(".review-rating-header.ground_service + td .star.fill"))
            wifi_connectivity = len(review.select(".review-rating-header.wifi_and_connectivity + td .star.fill"))
            value_for_money = len(review.select(".review-rating-header.value_for_money + td .star.fill"))
            recommended = review.select_one(".review-rating-header.recommended + td").get_text(strip=True).lower() == "yes"

            # 데이터 저장
            reviews_data.append({
                "Airline Name": airline_url.split("/")[-1].replace("-", " ").title(),
                "Overall Rating": overall_rating,
                "Review Title": title,
                "Review Date": review_date,
                "Author": author,
                "Review Content": content,
                "Type Of Traveller": traveller_type,
                "Seat Type": seat_type,
                "Route": route,
                "Date Flown": date_flown,
                "Seat Comfort": seat_comfort,
                "Cabin Staff Service": cabin_service,
                "Food & Beverages": food_beverages,
                "Inflight Entertainment": inflight_entertainment,
                "Ground Service": ground_service,
                "Wifi & Connectivity": wifi_connectivity,
                "Value For Money": value_for_money,
                "Recommended": "Yes" if recommended else "No"
            })

        print(f"    -> {len(review_sections)}개의 리뷰 수집 완료.")
        time.sleep(0)  # 요청 간격 조절
    return reviews_data

# 모든 항공사 리뷰 크롤링
def scrape_all_airlines(base_url, max_pages=3):
    airline_links = get_all_airline_links(base_url)
    all_reviews = []

    for airline_url in airline_links:
        print(f"현재 {airline_links.index(airline_url) + 1}/{len(airline_links)}개의 항공사를 크롤링 중입니다: {airline_url}")
        reviews = scrape_airline_reviews(airline_url, max_pages=max_pages)
        all_reviews.extend(reviews)

    return all_reviews

# 메인 실행
if __name__ == "__main__":
    base_url = "https://www.airlinequality.com/review-pages/a-z-airline-reviews/"
    all_reviews = scrape_all_airlines(base_url, max_pages=3)  # 각 항공사에서 최대 3페이지 크롤링

    # JSON 파일 저장
    output_file = "all_airline_reviews.json"
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(all_reviews, json_file, ensure_ascii=False, indent=4)
    print(f"크롤링 완료! 데이터를 {output_file}에 저장했습니다.")
