from sqlalchemy.orm import Session

cheerful_messages = [
    "Dive deep into this problem – your solution awaits!",
    "Every problem is an opportunity in disguise. Tackle it!",
    "Embrace the challenge – you're more capable than you think.",
    "Believe in your potential – this problem has a solution.",
    "A champion is made of perseverance. Show this problem what you've got!",
    "Growth happens outside your comfort zone. Push through!",
    "You've got the tools and the talent. Now, crack this problem!",
    "Problems are not stop signs; they're guidelines. Keep going!",
    "Every challenge you face is a step closer to mastery.",
    "The harder the problem, the sweeter the victory.",
    "Your best teacher is your last mistake. Learn and move forward!",
    "Success is the sum of small efforts. Keep chipping away!",
    "The best way to learn is to do. Dive in!",
    "Remember: every expert was once a beginner.",
    "One problem at a time, and you'll conquer them all.",
    "Coding is an art. Paint your masterpiece, one line at a time.",
    "Think. Code. Debug. Learn. Repeat.",
    "Challenges are what make life interesting. Overcoming them makes it meaningful.",
    "Be the coder who looks a challenge dead in the eye and gives it a wink.",
    "Mistakes are proof that you're trying. Keep pushing!",
    "The key to success? Persistence.",
    "Let this problem be a stepping stone, not a stumbling block.",
    "The code doesn't lie. If there's a solution, you'll find it!",
    "Every line of code you write brings you closer to the answer.",
    "With every problem you solve, you're leveling up.",
    "Coding isn't about being right, it's about getting it right. Iterate!",
    "You've got this! Trust the process and your abilities.",
    "In the face of adversity, let your code do the talking.",
    "The best way to predict the future is to code it.",
    "Remember why you started. Don't give up, find a way!"
]


def digitalize_problem_id(raw_pid: str | int):
    if type(raw_pid) is int:
        return raw_pid
    if raw_pid.isnumeric():
        return int(raw_pid)
    if not raw_pid[0] == "p" and raw_pid[1:].isdigit():
        return None
    return int(raw_pid[1:])

# async def range_check_problem_id(pid: int, session: Session):
#

