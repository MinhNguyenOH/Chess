"""
driver file, handle user input and display GameState object
"""
import pygame as p
from multiprocessing import Process, Queue
import SmartMoveFinder
import ChessEngine
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


WIDTH = HEIGHT = 480
DIMENSION = 8  # 8x8 chess board
MOVE_LOG_PANEL_WIDTH = 300
MOVE_LOG_PANEL_HEIGHT = HEIGHT

SQ_SIZE = HEIGHT // DIMENSION  # length each cell
MAX_FPS = 15  # animation stuff
IMAGES = {}


"""
Initialize a global dictionary of images, only called once in the main
"""


"""
FIX gameOver for undo move
"""


def loadImages():
    pieces = ["wp", "wR", "wN", "wB", "wK",
              "wQ", "bp", "bR", "bN", "bB", "bK", "bQ"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(
            "images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))


def main():
    p.init()
    screen = p.display.set_mode((WIDTH + MOVE_LOG_PANEL_WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    moveLogFont = p.font.SysFont("Arial", 20, False, False)

    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False  # flag variable for when a move is made
    animate = False  # flag var for when to animate a move
    loadImages()  # only do this once
    running = True
    sqSelected = ()  # no square selected initially, keep track of square clicked by user (tuple: (row, col))
    # keep track of player clicks (two tuples: [(6, 4), (4, 4)])
    playerClicks = []

    playerOne = False  # true when human playing white
    playerTwo = False  # for black
    AIThinking = False
    moveFinderProcess = None
    moveUndone = False
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (
            not gs.whiteToMove and playerTwo)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gs.gameOver and humanTurn:

                    location = p.mouse.get_pos()  # (x, y) location of mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    # user selected the same square or on move log panel
                    if sqSelected == (row, col) or col >= 8:
                        sqSelected = ()  # de-select
                        playerClicks = []  # clear player click
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)
                    if len(playerClicks) == 2:  # after 2nd click
                        move = ChessEngine.Move(
                            playerClicks[0], playerClicks[1], gs.board)
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]
            # key handlers
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # undo move as z
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                if e.key == p.K_r:  # reset board as r
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
        # AI move finder
        if not gs.gameOver and not humanTurn and not moveUndone:
            if not AIThinking:
                AIThinking = True
                print("AI thinking")
                returnQueue = Queue()
                moveFinderProcess = Process(
                    target=SmartMoveFinder.findBestMove, args=(gs, validMoves, returnQueue))
                moveFinderProcess.start()

            if not moveFinderProcess.is_alive():
                print("AI done thinking")
                AIMove = returnQueue.get()
                if AIMove is None:
                    AIMove = SmartMoveFinder.findRandomMove(validMoves)
                gs.makeMove(AIMove)
                moveMade = True
                animate = True
                AIThinking = False
        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False
        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont)

        if gs.checkMate or gs.staleMate:
            gs.gameOver = True
            text = "Stalemate" if gs.staleMate else "Black wins by checkmate" if gs.whiteToMove else "White wins by checkmate"
            drawEndGameText(screen, text)
        clock.tick(MAX_FPS)
        p.display.flip()


def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont):
    drawBoard(screen)  # draw squares on board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)
    drawMoveLog(screen, gs, moveLogFont)


def drawBoard(screen):
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(screen, color, p.Rect(
                c*SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        # sqSelected is piece that can move
        if gs.board[r][c][0] == ("w" if gs.whiteToMove else "b"):
            # highlight selected sq
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # transparancy value
            s.fill(p.Color("blue"))
            screen.blit(s, (c*SQ_SIZE, r * SQ_SIZE))
            # highlight valid moves
            s.fill(p.Color("yellow"))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol*SQ_SIZE, move.endRow*SQ_SIZE))


def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":  # not empty square
                screen.blit(IMAGES[piece], p.Rect(
                    c*SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawMoveLog(screen, gs, font):
    moveLogRect = p.Rect(WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("black"), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = str(i//2 + 1) + ". " + str(moveLog[i]) + " "
        if i + 1 < len(moveLog):  # ensure black made a move
            moveString += str(moveLog[i+1]) + " "
        moveTexts.append(moveString)
    movesPerRow = 3
    padding = 5
    lineSpacing = 2
    textY = padding
    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        for j in range(movesPerRow):
            if i + j < len(moveTexts):
                text += moveTexts[i+j]
        textObject = font.render(text, True, p.Color("White"))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing


def animateMove(move, screen, board, clock):
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10  # frames to move one square
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR*frame/frameCount,
                move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase piece moved from end square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol*SQ_SIZE,
                           move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        # draw captured piece onto rectangle
        if move.pieceCaptured != "--":
            if move.isEnpassantMove:
                enpassantRow = move.endRow + \
                    1 if move.pieceCaptured[0] == "b" else move.endRow - 1
                endSquare = p.Rect(move.endCol*SQ_SIZE,
                                   enpassantRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.pieceCaptured], endSquare)

        # draw moving piece
        if move.pieceMoved != "--":
            screen.blit(IMAGES[move.pieceMoved], p.Rect(
                c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvitca", 32, True, False)
    textObject = font.render(text, 0, p.Color("Gray"))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(
        WIDTH/2 - textObject.get_width()/2, HEIGHT/2 - textObject.get_height()/2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color("Black"))
    screen.blit(textObject, textLocation.move(2, 2))


if __name__ == "__main__":
    main()
