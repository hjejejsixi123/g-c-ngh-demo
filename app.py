"""Bản DEMO: web giúp học sinh THPT đối mặt áp lực học tập.
Chỉ thử bằng tình huống giả định, chưa dùng cho học sinh thật."""
import os
import re
import unicodedata

SYSTEM_PROMPT = """Bạn là trợ lý AI (không phải người, không phải chuyên gia tâm lý)
giúp học sinh THPT Việt Nam đối mặt áp lực học tập.
- Xưng "mình", gọi "bạn". Trả lời ngắn, ấm áp, không phán xét.
- Mỗi lượt hỏi tối đa 1 câu gợi mở. Giúp học sinh tự gọi tên cảm xúc,
  nhìn nhiều phía và chọn một việc nhỏ để làm.
- Không chẩn đoán, không kê thuốc, không hứa giữ bí mật tuyệt đối.
- Không níu kéo người dùng. Khuyến khích kết nối với người thật.
- Nếu có dấu hiệu tự hại, tự tử, bạo hành, xâm hại: hỏi em có đang an toàn không,
  khuyên tìm ngay người lớn tin cậy, gọi 111; nguy cấp thì gọi 115."""

# Lưới lọc thô: vẫn sẽ bỏ sót và báo nhầm.
DANGER = [
    r"tự tử", r"tự sát", r"muốn chết", r"không muốn sống", r"chán sống",
    r"tự làm (đau|hại)", r"kết thúc cuộc đời", r"biến mất mãi",
    r"bị (đánh|bạo hành|xâm hại|sàm sỡ|đe d[oọ]a)",
    r"(không|khong|ko|k) (muốn|muon|mún|mun) (sống|song)", r"ngủ mãi (không|ko|k) (dậy|tỉnh)",
    r"\btu tu\b", r"muon chet", r"khong muon song",
]

SAFETY_REPLY = (
    "Mình lo cho sự an toàn của bạn. Mình là AI nên không thể đến bên bạn được. "
    "Ngay lúc này, bạn hãy tìm một người lớn tin cậy (bố mẹ, người thân, thầy cô) "
    "và nói rằng bạn cần họ ở cạnh. Bạn có thể gọi **111** (Tổng đài bảo vệ trẻ em). "
    "Nếu đang nguy hiểm, hãy gọi **115** hoặc nhờ người gần nhất giúp. "
    "Bây giờ bạn có đang an toàn không, và có ai ở gần bạn không?"
)

SCENARIOS = {
    "Điểm thấp hơn mong đợi": "Bạn ôn rất kỹ nhưng bài kiểm tra chỉ được 5 điểm.",
    "Bị so sánh": "Bố mẹ nói: 'Con nhà người ta được học sinh giỏi kìa.'",
    "Chọn ngành": "Bạn thích thiết kế, gia đình muốn bạn học ngành khác.",
}


def is_danger(text: str) -> bool:
    t = unicodedata.normalize("NFC", text.lower())
    return any(re.search(p, t) for p in DANGER)


def ask_ai(history):
    key, model = os.getenv("AI_API_KEY"), os.getenv("AI_MODEL")
    if not key or not model:
        return ("(Chế độ demo, chưa nối AI) Nghe có vẻ bạn đang bận lòng. "
                "Điều gì trong chuyện này làm bạn áp lực nhất?")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key, base_url=os.getenv("AI_BASE_URL") or None)
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history[-12:],
        )
        return res.choices[0].message.content
    except Exception:
        return ("Mình đang bị lỗi kết nối. Nếu chuyện gấp, hãy tìm người lớn tin cậy, "
                "gọi 111, hoặc 115 khi nguy hiểm.")


def main():
    import streamlit as st

    st.set_page_config(page_title="Góc Nghĩ (demo)")
    st.title("Góc Nghĩ")
    st.caption("Bản demo. Đây là AI, không phải chuyên gia tâm lý. "
               "Đừng nhập tên, trường, số điện thoại hay chuyện thật của bạn.")
    st.sidebar.error("**Cần giúp ngay?**\n\nTìm người lớn tin cậy.\n\n"
                     "Gọi **111** (bảo vệ trẻ em) hoặc **115** (cấp cứu).")

    chat_tab, scene_tab = st.tabs(["Check-in và trò chuyện", "Tình huống"])

    with chat_tab:
        mood = st.select_slider(
            "Hôm nay bạn thấy thế nào?",
            ["Rất tệ", "Tệ", "Bình thường", "Ổn", "Rất ổn"], value="Bình thường")
        if mood == "Rất tệ":
            st.warning("Nếu bạn thấy không an toàn, hãy tìm người lớn ngay hoặc gọi 111.")
        history = st.session_state.setdefault("history", [])
        box = st.container()
        text = st.chat_input("Điều gì đang làm bạn bận lòng?")
        if text:
            history.append({"role": "user", "content": text})
            reply = SAFETY_REPLY if is_danger(text) else ask_ai(history)
            history.append({"role": "assistant", "content": reply})
        for m in history:
            box.chat_message(m["role"]).markdown(m["content"])

    with scene_tab:
        name = st.selectbox("Chọn tình huống", list(SCENARIOS))
        st.info(SCENARIOS[name])
        answers = [
            st.text_area("1. Bạn có thể cảm thấy gì?", key=name + "1"),
            st.text_area("2. Còn cách nhìn nào khác không?", key=name + "2"),
            st.text_area("3. Một việc nhỏ bạn có thể làm là gì?", key=name + "3"),
        ]
        if st.button("Xem lại suy nghĩ của mình"):
            if is_danger(" ".join(answers)):
                st.error(SAFETY_REPLY)
            elif all(a.strip() for a in answers):
                st.success("Bạn đã đi qua đủ 3 bước: cảm xúc, góc nhìn, hành động. "
                           "Bạn muốn chia sẻ việc nhỏ đó với ai?")
            else:
                st.write("Bạn thử trả lời đủ 3 câu nhé.")


if __name__ == "__main__":
    main()
