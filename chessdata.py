#a code meant to analyze set of games from pgn files and giving feedback based on positions that need to be worked on
Games={}
class Cleangame():
    def __init__(self,white,black,move,score):
        self.white=white
        self.black=black
        self.move=move
        self.score=score
    def show(self):
        return f"This is a game between: {self.white[0]} and {self.black[0]} moves: {Cleangame.show_moves(self)}"
    def show_moves(self):
        movestring=""
        for ply in self.move:
            movestring+=ply.show()
        return movestring
class Move():
    def __init__(self,piece,move,colour,takes):
        self.piece=piece
        self.move=move
        self.colour=colour
        self.takes=takes
    def show(self):
        if not self.takes:
            return f"{self.colour} {self.piece} to {self.move}\n"
        return f"{self.colour} {self.piece} takes on {self.move}\n"
def createmove(move,movenr):
    takes=0
    print(move[0])
    if move[0].islower(): piece="pawn"
    else:
        if move[0]=="N":
            piece="knight"
            move=move[1:]
        elif move[0]=="B":
            piece="bishop"
            move=move[1:]
        elif move[0]=="R":
            piece="rook"
            move=move[1:]
        elif move[0]=="Q":
            piece="queen"
            move=move[1:]
        elif move[0]=="K" or move[0]=="O":
            piece="king"
            if not move[0]=="0":
                move=move[1:]
    #to turn into switch soon
    if "x" in move:
        takes=1
        move= move.split("x")[1]
    if movenr%2:colour="White"
    else: colour="Black"
    return Move(piece,move,colour,takes)
def separate(notation: list)-> list:
    game=[]
    for nr,move in enumerate(notation):
        game.append(createmove(move,nr))
    return game
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
                game=separate(moves[:-1])
                Games[count]=Cleangame(headers["White"],headers["Black"],game,moves[-1])
                moves=[]
                headers.clear()
                count+=1
    for nr,game in Games.items():
        print(f"Game number {nr}\n{Games[nr].show()}")

def get():
    pass
def main():
    pass
if __name__=="__main__":
    parse_games()