# ================================================
# プロトタイプ（pt） 行列式因数分解ゲーム
# ================================================
import streamlit as st
import json
import sympy as sp
from sympy import Matrix, symbols, latex, sympify
import time
import os
import re
import unicodedata

# ====== ページ設定 ======
st.set_page_config(layout="wide")

# 画面を3つのカラムに分割
left, center, right = st.columns([1, 2, 1])

# ====== タイトル ======
with center:
    st.title("行列式因数分解ゲーム（pt0）")

x = symbols('x')

# ====== 関数：行列データ読み込み ======
def load_matrix_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        matrix = Matrix(data["matrix"])
        size = matrix.shape[0]
    return size, matrix, data

# ====== 関数：デモ用サンプル行列 ======
def demo_matrix():
    matrix = Matrix([[-x+1, 4, -4],
                     [-3, -x+1, 3],
                     [-3, 4, -x]])
    return 3, matrix, {"matrix": matrix.tolist()}

# ====== セッション初期化 ======
for key, default in {
    "factor": 1,
    "matrix": None,
    "size": None,
    "problem_data": None,
    "last_file": None,
    "start_time": time.time(),
}.items():
    st.session_state.setdefault(key, default)

# 最初は必ずデモ問題
if st.session_state.matrix is None:
    size, matrix, data = demo_matrix()
    st.session_state.size = size
    st.session_state.matrix = matrix
    st.session_state.problem_data = data
    st.session_state.last_file = "demo"

# ====== 問題ファイル選択（プルダウン） ======
with center:
    # ディレクトリ内の problem*.json をリストアップ
    problem_files = [f for f in os.listdir(".") if f.startswith("problem") and f.endswith(".json")]
    if problem_files:
        selected_file = st.selectbox("問題ファイルを選んでな:", ["デモ"] + problem_files, index=0)

        if selected_file != st.session_state.last_file:
            if selected_file == "デモ":
                size, matrix, data = demo_matrix()
            else:
                size, matrix, data = load_matrix_from_file(selected_file)
            st.session_state.size = size
            st.session_state.matrix = matrix
            st.session_state.problem_data = data
            st.session_state.last_file = selected_file
            st.session_state.factor = 1
            st.session_state.start_time = time.time()

# ====== タイマー表示 ======
with center:
    if st.session_state.start_time is not None:
        elapsed_time = time.time() - st.session_state.start_time
        minutes = int(elapsed_time / 60)
        seconds = int(elapsed_time % 60)
        st.write(f"経過時間：{minutes}分 {seconds}秒")

# ==============================
# 【操作パネル：行の入れ替え】
# ==============================
with left:
    st.subheader("行の入れ替え")
    row1 = st.number_input("入れ替える行1 (1〜n)", min_value=1, max_value=st.session_state.size, value=1, key="swap_row1")
    row2 = st.number_input("入れ替える行2 (1〜n)", min_value=1, max_value=st.session_state.size, value=2, key="swap_row2")
    if st.button("行を入れ替える", key="swap_button"):
        st.session_state.matrix[row1-1, :], st.session_state.matrix[row2-1, :] = \
        st.session_state.matrix[row2-1, :], st.session_state.matrix[row1-1, :]
        st.session_state.factor *= -1

# ==============================
# 【操作パネル：行同士の加減】
# ==============================
with right:
    st.subheader("行同士の加減")
    src_row = st.number_input("加減元の行 (1〜n)", min_value=1, max_value=st.session_state.size, value=1, key="add_src_row")
    dest_row = st.number_input("加減先の行 (1〜n)", min_value=1, max_value=st.session_state.size, value=2, key="add_dest_row")
    factor_str = st.text_input("係数（例: 2, -1, x-1）", value="1", key="add_factor_str")

    if st.button("行を加減する", key="add_button"):
        try:
            normalized_factor_str = unicodedata.normalize('NFKC', factor_str)
            def simplify_input_string(s):
                s = s.replace('^', '**')
                s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
                s = re.sub(r'([a-zA-Z])(\d)', r'\1**\2', s)
                s = re.sub(r'([a-zA-Z])([a-zA-Z])', r'\1*\2', s)
                return s
            processed_factor_str = simplify_input_string(normalized_factor_str)
            factor_expr = sp.sympify(processed_factor_str)
            st.session_state.matrix[dest_row-1, :] += factor_expr * st.session_state.matrix[src_row-1, :]
            st.success("行の加減操作、完了したで！")
        except sp.SympifyError:
            st.error("その文字列は数式として認識できへんで")
        except Exception as e:
            st.error(f"エラーや: {e}")

# ==============================
# 【操作パネル：転置】
# ==============================
with right:
    st.subheader("転置")
    if st.button("転置する", key="btn_transpose"):
        st.session_state.matrix = st.session_state.matrix.copy().T

# ==============================
# 【操作パネル：共通因数くくり出し】
# ==============================
with left:
    st.subheader("共通因数くくり出し")
    factor_row = st.number_input("因数をくくる行", min_value=1, max_value=st.session_state.size, value=1, key="factor_row")
    factor_str = st.text_input("くくり出す因数（例: x-1, 2）", value="", key="factor_str")

    if st.button("因数くくり出し", key="btn_factor"):
        if not factor_str:
            st.warning("くくり出す因数を入力してや")
        else:
            try:
                normalized_factor_str = unicodedata.normalize('NFKC', factor_str)
                def simplify_input_string(s):
                    s = s.replace('^', '**')
                    s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
                    s = re.sub(r'([a-zA-Z])(\d)', r'\1**\2', s)
                    s = re.sub(r'([a-zA-Z])([a-zA-Z])', r'\1*\2', s)
                    return s
                processed_factor_str = simplify_input_string(normalized_factor_str)
                factor_expr = sp.sympify(processed_factor_str)
                m = st.session_state.matrix.copy()
                row_index = factor_row - 1
                can_factor_out = True
                for j in range(m.shape[1]):
                    quotient, remainder = sp.div(m[row_index, j], factor_expr, domain='QQ')
                    if remainder != 0:
                        can_factor_out = False
                        break
                    m[row_index, j] = quotient
                if can_factor_out:
                    st.session_state.matrix = m
                    st.session_state.factor = sp.simplify(st.session_state.factor * factor_expr)
                    st.success(f"成功！因数 `{factor_expr}` をくくり出したで！")
                else:
                    st.error(f"エラーやで `{factor_expr}` は、この行全部の共通因数ちゃうみたいや")
            except sp.SympifyError:
                st.error("入力した文字列は数式とちゃうで")
            except Exception as e:
                st.error(f"予期せぬエラーや: {e}")

# ====== 現在の状態表示 ======
with center:
    st.subheader("現在の行列式")
    if st.session_state.matrix is not None:
        expr_factor = latex(simpify(st.session_state.factor))
        expr_matrix = latex(st.session_state.matrix)
        st.latex(rf"{expr_factor} \cdot {expr_matrix}")

# ==============================
# 【ゴール判定】
# ==============================
with center:
    current_det = st.session_state.matrix.det() if st.session_state.matrix is not None else None

    if current_det is not None and not current_det.free_symbols:
        st.success(f"おめでとうさん！🎉 残った行列式は数になったで！")
        st.write(f"最終的な行列式の値は `{st.session_state.factor * current_det}` やで")
        final_time = time.time() - st.session_state.start_time
        final_minutes = int(final_time / 60)
        final_seconds = int(final_time % 60)
        st.write(f"クリアタイム：{final_minutes}分 {final_seconds}秒")

        # ------------------------------
        # 風船演出（初回のみ）
        # ------------------------------
        if "cleared" not in st.session_state:
            st.session_state.cleared = False

        if not st.session_state.cleared:
            if final_minutes < 3:
                for _ in range(10):
                    st.balloons()
                    time.sleep(0.5)
            elif final_minutes < 5:
                for _ in range(5):
                    st.balloons()
                    time.sleep(0.5)
            elif final_minutes < 7:
                for _ in range(3):
                    st.balloons()
                    time.sleep(0.5)
            elif final_minutes < 10:
                st.balloons()
            else:
                st.snow()
            st.session_state.cleared = True   # ← ここで「演出済み」マーク

        # ==============================
        # 【もう1回やるか？ボタン（ゴール後のみ表示）】
        # ==============================
        reset = st.button("もう1回やるか？")
        if reset:
            size, matrix, data = demo_matrix()
            st.session_state.update({
                "factor": 1,
                "matrix": matrix,
                "size": size,
                "problem_data": data,
                "last_file": "demo",
                "start_time": time.time(),
                "cleared": False  # ← リセット時に解除
            })
            st.rerun()
    else:
        st.info("まだゴールちゃうで。行列式が数字になるまで頑張ってな！")

