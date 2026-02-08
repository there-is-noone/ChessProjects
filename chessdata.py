#a code meant to analyze set of games from pgn files and giving feedback based on positions that need to be worked on
Games={}
class Cleangame():
    def __init__(self,white,black,move):
        self.white=white
        self.black=black
        self.move=move
    def show(self):
        return f"This is a game between: {self.white[0]} and {self.black[0]} and it went like this: \n {self.move}"
    def verifygame(self):
        pass
def parse_games():
    headers={}
    gamestart=False
    moves=[]
    count=0
    file = open(f"/home/kkrec/chessgames/Berliner.pgn", "r")
    for line in file:
        if line.startswith("1."):
            gamestart=True
        elif line.startswith("["):
            line1=line.replace("[","")
            line1=line1.replace("]","")
            line1=line1.replace("\n","").split(" ", 1)
            print(line1)
            headers[line1[0]]=line1[1:]
        if gamestart:
            line1=line.split(" ")
            line1=[a.replace("\n","").split(".")[-1] for a in line1]
#            print(line1)
            moves+=line1
            if line=="\n":
                gamestart=False
                moves=[a for a in moves if a]
                Games[count]=Cleangame(headers["White"],headers["Black"],moves)
                moves=[]
                headers.clear()
                count+=1
    for nr,game in Games.items():
        print(f"Game number {nr}\n{Games[nr].show()}")
def separate():
    pass
def get():
    pass
def main():
    pass
if __name__=="__main__":
    parse_games()