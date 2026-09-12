from quests.ai import generate_quest

quest = generate_quest()
print(quest.text)
print(quest.difficulty)
print(quest.category)