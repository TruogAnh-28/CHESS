"""
Tập tin chính điều khiển.
Xử lý đầu vào từ người dùng.
Hiển thị trạng thái hiện tại của đối tượng GameStatus.
"""
import pygame as p
import ChessEngine, ChessAI
import sys
from multiprocessing import Process, Queue
import playsound as pg
BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

played = False
def loadImages():
    """
    Khởi tạo một thư mục toàn cục các hình ảnh.
    Hàm này chỉ được gọi một lần trong hàm main.
    """
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))


def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("White"))
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False
    animate = False
    loadImages()
    running = True
    square_selected = ()
    player_clicks = []
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    move_log_font = p.font.SysFont("Arial", 14, False, False)
    player_one = False
    player_two = True
    player_rect, AI_rect = displayModeSelectionMenu(screen)
    
    AI_random_white =False
    AI_random_black =False
    # Chờ người chơi chọn màu
    color_selected = None
    mode_selector=None
    while mode_selector is None:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                mouse_pos = p.mouse.get_pos()
                if player_rect.collidepoint(mouse_pos):
                    mode_selector = 'player'
                elif AI_rect.collidepoint(mouse_pos):
                    mode_selector = 'AI'
    white_rect, black_rect = displayColorSelectionMenu(screen)
    while color_selected is None:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                mouse_pos = p.mouse.get_pos()
                if white_rect.collidepoint(mouse_pos):
                    color_selected = 'white'
                elif black_rect.collidepoint(mouse_pos):
                    color_selected = 'black'
    if color_selected == 'white' and mode_selector == 'player':
        player_one = True
        player_two = False
    elif color_selected == 'black' and mode_selector == 'player':
        player_one = False
        player_two = True
    elif color_selected == 'white' and mode_selector == 'AI':
        player_one = False
        player_two = False
        AI_random_white = True
        AI_random_black = False
    elif color_selected == 'black' and mode_selector == 'AI':
        player_one = False
        player_two = False
        AI_random_black = True
        AI_random_white = False
    
    screen.fill(p.Color("black"))
    while running:
        switch_rect ,undo_button_rect,restart_button_rect =displayButtons(screen)  # Hiển thị các nút
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        AI_random_turn = (game_state.white_to_move and AI_random_white) or (not game_state.white_to_move and AI_random_black)
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                mouse_pos = p.mouse.get_pos()
                if switch_rect.collidepoint(mouse_pos):  # Xử lý khi nhấn nút "Switch Color"
                        player_one,player_two,AI_random_white,AI_random_black = handleSwitchColorButtonClick(screen,color_selected,mode_selector)
                        game_state = ChessEngine.GameState()
                        valid_moves = game_state.getValidMoves()
                        square_selected = ()
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        if ai_thinking:
                            move_finder_process.terminate()
                            ai_thinking = False
                        move_undone = False 
                elif undo_button_rect.collidepoint(mouse_pos):  # Xử lý khi nhấn nút "Undo Move"
                        game_state.undoMove()
                        move_made = True
                        animate = False
                        game_over = False
                        if ai_thinking:
                            move_finder_process.terminate()
                            ai_thinking = False
                        move_undone = True
                elif restart_button_rect.collidepoint(mouse_pos):  # Xử lý khi nhấn nút "Restart Game"
                        game_state = ChessEngine.GameState()
                        valid_moves = game_state.getValidMoves()
                        square_selected = ()
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        if ai_thinking:
                            move_finder_process.terminate()
                            ai_thinking = False
                        move_undone = False 
                if not game_over: 
                        location = p.mouse.get_pos()
                        col = location[0] // SQUARE_SIZE
                        row = location[1] // SQUARE_SIZE
                        if square_selected == (row, col) or col >= 8:
                            square_selected = ()
                            player_clicks = []
                        else:
                            square_selected = (row, col)
                            player_clicks.append(square_selected)
                        if len(player_clicks) == 2 and human_turn:
                            move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                            for i in range(len(valid_moves)):
                                if move == valid_moves[i]:
                                    game_state.makeMove(valid_moves[i])
                                    move_made = True
                                    animate = True
                                    square_selected = ()
                                    player_clicks = []
                            if not move_made:
                                player_clicks = [square_selected]
        if AI_random_turn:
            if valid_moves:
                AI_random_move = ChessAI.findRandomMove(valid_moves)
                game_state.makeMove(AI_random_move)
                move_made = True
                animate = True
        elif not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                    ai_thinking = True
                    return_queue = Queue()
                    move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))
                    move_finder_process.start()

            if not move_finder_process.is_alive():
                    ai_move = return_queue.get()
                    if ai_move is None:
                        ai_move = ChessAI.findRandomMove(valid_moves)
                    game_state.makeMove(ai_move)
                    move_made = True
                    animate = True
                    ai_thinking = False

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)

        # if not game_over:
        #     drawMoveLog(screen, game_state, move_log_font)
        global played
        if game_state.checkmate:
            
            game_over = True
            if not played:
                played=True
                pg.playsound("sound/endsound.mp3")
            if game_state.white_to_move:
                drawEndGameText(screen, "Black wins, number of turn: {}".format(len(game_state.move_log) // 2))   
            else:
                drawEndGameText(screen, "White wins, number of turn: {}".format(len(game_state.move_log) // 2))

        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()




def displayColorSelectionMenu(screen):
    font_title = p.font.SysFont("Helvetica", 48, True, False)
    font_button = p.font.SysFont("Helvetica", 32, True, False)
    button_width = 200
    button_height = 50
    button_margin = 80
    
    screen_width, screen_height = screen.get_size()
    button_start_x = (screen_width - (button_width * 2 + button_margin)) // 2
    button_start_y = (screen_height - button_height) // 2 +50
    
    # Hiển thị tiêu đề "Chess Game"
    title_text = font_title.render("Chess Game", True, p.Color("white"))
    title_rect = title_text.get_rect(center=(screen_width // 2, 100))
    screen.fill(p.Color("black"))
    # Tạo nút "Play as White"
    button_white_rect = create_button(screen, button_start_x, button_start_y, button_width, button_height, "Play as White", font_button, button_color=(255, 255, 255), border_color=(0, 0, 0))
    
    # Tạo nút "Play as Black"
    button_black_rect = create_button(screen, button_start_x + button_width + button_margin, button_start_y, button_width, button_height, "Play as Black", font_button, button_color=(255, 255, 255), border_color=(0, 0, 0))
    
    # Hiển thị tiêu đề và nút

    screen.blit(title_text, title_rect)
    p.display.flip()
    
    return button_white_rect, button_black_rect
def displayModeSelectionMenu(screen):
    font_title = p.font.SysFont("Helvetica", 48, True, False)
    font_button = p.font.SysFont("Helvetica", 32, True, False)
    button_width = 200
    button_height = 50
    button_margin = 80
    
    screen_width, screen_height = screen.get_size()
    button_start_x = (screen_width - (button_width * 2 + button_margin)) // 2
    button_start_y = (screen_height - button_height) // 2 +50
    
    # Hiển thị tiêu đề "Chess Game"
    title_text = font_title.render("Chess Game", True, p.Color("white"))
    title_rect = title_text.get_rect(center=(screen_width // 2, 100))
    screen.fill(p.Color("black"))
    # Tạo nút "Play as White"
    player_rect = create_button(screen, button_start_x, button_start_y, button_width, button_height, "Player", font_button, button_color=(255, 255, 255), border_color=(0, 0, 0))
    
    # Tạo nút "Play as Black"
    AI_rect = create_button(screen, button_start_x + button_width + button_margin, button_start_y, button_width, button_height, "AI random", font_button, button_color=(255, 255, 255), border_color=(0, 0, 0))
    
    # Hiển thị tiêu đề và nút

    screen.blit(title_text, title_rect)
    p.display.flip()
    
    return player_rect, AI_rect
def handleSwitchColorButtonClick(screen, color_selected, mode_selector):
    if color_selected == 'white' and mode_selector == 'player':
        player_one = False
        player_two = True
    elif color_selected == 'black' and mode_selector == 'player':   
        player_one = True
        player_two = False
    elif color_selected == 'white' and mode_selector == 'AI':
        player_one = False
        player_two = False
        AI_random_black = True
        AI_random_white = False
    elif color_selected == 'black' and mode_selector == 'AI':  
        player_one = False
        player_two = False
        AI_random_white = True
        AI_random_black = False
    return player_one,player_two,AI_random_white,AI_random_black
def create_button(screen, x, y, width, height, text, font, text_color=(0, 0, 0), button_color=(255, 255, 255), border_color=None):
    button_rect = p.Rect(x, y, width, height)

    # Vẽ nền của nút
    p.draw.rect(screen, button_color, button_rect)

    # Vẽ viền của nút nếu có
    if border_color:
        p.draw.rect(screen, border_color, button_rect, 2)  # 2 là độ dày của viền

    # Hiển thị văn bản trên nút
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)

    return button_rect
def displayButtons(screen):
    font = p.font.SysFont("Helvetica", 24, True, False)
    button_width = 150
    button_height = 40
    button_margin = 20
    screen_width, screen_height = screen.get_size()
    
    
    # Tạo nút "Undo Move"
    undo_button_rect = create_button(screen, screen_width - button_width - button_margin -30, screen_height - button_margin - button_height, button_width, button_height, "Undo Move", font, button_color=(255, 255, 255), border_color=(0, 0, 0))
    
    # Tạo nút "Restart Game"
    restart_button_rect = create_button(screen, screen_width - button_width - button_margin -30 , screen_height - button_margin * 2 - button_height * 2, button_width, button_height, "Restart Game", font, button_color=(255, 255, 255), border_color=(0, 0, 0))
    
    switch_rect = create_button(screen, screen_width - button_width - button_margin -30, screen_height - button_margin*3  -  button_height*3, button_width, button_height, "Switch Color", font, button_color=(255, 255, 255), border_color=(0, 0, 0))
    
    p.display.flip()
    
    return switch_rect, undo_button_rect, restart_button_rect






def drawGameState(screen, game_state, valid_moves, square_selected):
    """
    Đảm nhận toàn bộ đồ họa trong trạng thái trò chơi hiện tại.
    """
    drawBoard(screen)  # vẽ các ô trên bàn cờ
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)  # vẽ các quân cờ lên các ô đó


def drawBoard(screen):
    """
    Vẽ các ô trên bàn cờ.
    Ô trên bên trái luôn luôn là sáng.
    """
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    Đánh dấu ô được chọn và các nước đi cho quân cờ được chọn.
    """
    if (len(game_state.move_log)) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == (
                'w' if game_state.white_to_move else 'b'):  # square_selected là một quân cờ có thể được di chuyển
            # đánh dấu ô đã chọn
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)  # giá trị độ trong suốt 0 -> trong suốt, 255 -> không trong suốt
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            # đánh dấu các nước đi từ ô đó
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))


def drawPieces(screen, board):
    """
    Vẽ các quân cờ trên bàn cờ sử dụng game_state.board hiện tại
    """
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def drawMoveLog(screen, game_state, font):
    """
    Hiện bảng ghi chú nước đi.

    """
    MOVE_LOG_PANEL_HEIGHT = 200  # Chiều cao mới của bảng ghi chú
    
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing



def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("red"))
    text_location = p.Rect(30, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    # text_object = font.render(text, False, p.Color('red'))
    screen.blit(text_object, text_location.move(2, 2))


def animateMove(move, screen, board, clock):
    """
    Thực hiện hiệu ứng cho một nước đi
    """
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10  # số khung hình để di chuyển một ô
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # xóa quân cờ đã di chuyển khỏi ô đích
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        # vẽ quân cờ đã bị bắt lên hình chữ nhật
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        # vẽ quân cờ đang di chuyển
        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
