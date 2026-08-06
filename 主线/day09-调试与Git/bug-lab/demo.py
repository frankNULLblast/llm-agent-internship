from scores import average, grade, load_scores


print("empty average:", average([]))
print("scores:", load_scores("成绩.json"))
print("60 is:", grade(60))
