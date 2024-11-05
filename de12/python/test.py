for i in range(3): #コロンが入っていることに注意
    print(i,"人目") #タブでずらしていることに注意！

    name=input("aaa")
    waist=float(input("腹囲は？"))
    age=input("年齢は？")

    print(name, "さんは腹囲", waist, "cmで年齢は",age, "才ですね。")

    if waist>=80:
    print(name,"さん、内臓脂肪蓄積注意です")
    else:
    print(name,"さん、腹囲は問題ありません")


# 出力結果
# 0 人目
# 1 人目
# 2 人目
