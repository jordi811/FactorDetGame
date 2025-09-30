# ================================================
# プロトタイプ0（pt0） 行列式因数分解ゲーム
# ================================================
import streamlit as st
import json
import numpy as np
import sympy as sp
from sympy import Matrix, symbols, latex
import time
import re
import os

# ====== ページ設定 ======
st.set_page_config(layout="wide")

# 画面を3つのカラムに分割する
# 比率を調整して、左と右にパネル、真ん中に行列を配置
left, center, right = st.columns([1, 2, 1])

# ====== タイトル ======
with center:
    st.title("行列式因数分解ゲーム（pt0）")

x = symbols('x')

# ====== 関数：行列データ読み込み ======
def load_matrix(uploaded_file):
    data = json.load(uploaded_file)
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
with center:
if "matrix" not in st.session_state:
    # 同じディレクトリにある problem*.json を探す
    problem_files = [f for f in os.listdir(".") if f.startswith("problem") and f.endswith(".json")]

    # プルダウンで選択
    selected_file = st.selectbox("問題ファイルを選んでな:", problem_files)

    if selected_file:
        # 選ばれたファイルを open() で読み込む
        with open(selected_file, "r", encoding="utf-8") as f:
            size, matrix, data = load_matrix(f)
    else:
        st.info("ファイル選ばれてへんから、デモ用の行列を使うで")
        time.sleep(10)
        size, matrix, data = demo_matrix()

        st.session_state.size = size
        st.session_state.matrix = matrix
        st.session_state.factor = 1
        st.session_state.start_time = time.time()

# ====== タイマー表示 ======
with center:
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
# 【操作パネル：行の加減】
# ==============================
with right:
    st.subheader("行同士の加減")
    src_row = st.number_input("加減元の行 (1〜n)", min_value=1, max_value=st.session_state.size, value=1, key="add_src_row")
    dest_row = st.number_input("加減先の行 (1〜n)", min_value=1, max_value=st.session_state.size, value=2, key="add_dest_row")
# ここを st.text_input に変更！
    factor_str = st.text_input("係数（例: 2, -1, x-1）", value="1", key="add_factor_str")

    if st.button("行を加減する", key="add_button"):
        try:
        # 全角文字を半角に変換
            import unicodedata
            normalized_factor_str = unicodedata.normalize('NFKC', factor_str)
        
        # SymPyが理解できる形式に変換
            import re
            def simplify_input_string(s):
                s = s.replace('^', '**')
                s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
                s = re.sub(r'([a-zA-Z])(\d)', r'\1**\2', s)
                s = re.sub(r'([a-zA-Z])([a-zA-Z])', r'\1*\2', s)
                return s
        
            processed_factor_str = simplify_input_string(normalized_factor_str)
        
        # SymPyの式として認識させる
            factor_expr = sp.sympify(processed_factor_str)
        
        # 行の加減操作を実行
            st.session_state.matrix[dest_row-1, :] += factor_expr * st.session_state.matrix[src_row-1, :]
            st.success("行の加減操作、完了したで！")
    
        except sp.SympifyError:
            st.error("あかん！その文字列は、ちゃんとした数式とちゃうで")
        except Exception as e:
            st.error(f"残念やけど、エラーやわ: {e}")

# ==============================
# 【操作パネル：行列の転置】
# ==============================
with right:
    st.subheader("**転置**")
    if st.button("転置する", key="btn_transpose"):
        m = st.session_state.matrix.copy().T
        st.session_state.matrix = m

# ==============================
# 【操作パネル：共通因数のくくり出し】
# ==============================
with left:
    st.subheader("**共通因数くくり出し（数値 or 数式）**")
    factor_row = st.number_input("因数をくくる行", min_value=1, max_value=st.session_state.size, value=1, key="factor_row")
# 入力欄の初期値を変更して、ユーザーに分かりやすくする
    factor_str = st.text_input("くくり出す因数（例: x-1, 2）", value="", key="factor_str")

    if st.button("因数くくり出し", key="btn_factor"):
        if not factor_str:
            st.warning("くくり出す因数を入力してや")
        else:
            try:
            # ユーザーの入力文字列をSymPyが理解できる形式に変換
                def simplify_input_string(s):
                # べき乗を^から**に変換
                    s = s.replace('^', '**')
                # 2x -> 2*x, ax -> a*x のように、文字と数字や文字の間の掛け算記号を追加
                    s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
                    s = re.sub(r'([a-zA-Z])(\d)', r'\1**\2', s) # a2 -> a**2
                    s = re.sub(r'([a-zA-Z])([a-zA-Z])', r'\1*\2', s)
                    return s

                import unicodedata
            # 全角文字を半角に、そしてSymPy形式に変換
                normalized_factor_str = unicodedata.normalize('NFKC', factor_str)
                processed_factor_str = simplify_input_string(normalized_factor_str)
            
                factor_expr = sp.sympify(processed_factor_str)
            
                m = st.session_state.matrix.copy()
                row_index = factor_row - 1
            
            # 割り切れるかどうかのフラグ
                can_factor_out = True
            
                for j in range(m.shape[1]):
                # sp.div()で割り算して、商と余りを取得
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
                    st.info("その因数、合ってるかもう一回見てみよか")

            except sp.SympifyError:
                st.error("入力してもろたんは、数式とちゃうわ。半角英数字で、もう一回入れてみてな！")
            except Exception as e:
                st.error(f"あかんわ。なんか予期せぬエラーが出たみたいや: {e}")

# ====== 現在の状態表示 ======
with center:
    st.subheader("現在の行列式")
    st.latex(rf"{st.session_state.factor} \cdot {latex(st.session_state.matrix)}")

# ==============================
# 【ゴール判定】
# ==============================
with center:
    st.subheader("ゴール判定")
    current_det = st.session_state.matrix.det()

# 行列式にxが含まれていないかチェック
    if not current_det.free_symbols:
    # 完全に数値だけになったら、ゴールを宣言
        st.success(f"おめでとうさん！🎉 残った行列式は数になったで！")
        st.write(f"最終的な行列式の値は `{st.session_state.factor * current_det}` やで")
    # タイマーの最終時間を表示
        final_time = time.time() - st.session_state.start_time
        final_minutes = int(final_time / 60)
        final_seconds = int(final_time % 60)
        st.write(f"クリアタイム：{final_minutes}分 {final_seconds}秒")
        # クリアタイムに応じて風船の回数を調整
        if final_minutes < 3:
            for _ in range(10):
                st.balloons()
                time.sleep(0.5) #
        elif final_minutes < 5:
            for _ in range(5):
                st.balloons()
                time.sleep(0.5) #
        elif final_minutes < 7:
            for _ in range(3):
                st.balloons()
                time.sleep(0.5) #
        elif final_minutes < 10:
            st.balloons()
        else:
            st.snow() # 15分以上やったら雪を降らせる
    else:

        st.info("まだゴールちゃうで。行列式が数字になるまで、もうちょい頑張ってな！")
