# coding: utf-8
import clr
import os
import random

clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')
clr.AddReference('PresentationCore')

import System
import System.Windows.Threading

from System.Windows import Window, Thickness, VerticalAlignment, HorizontalAlignment
from System.Windows.Controls import Grid, Button, Image, StackPanel, Label, TextBox
from System.Windows.Media import Brushes, ImageSourceConverter, Stretch
from System.Windows.Input import MouseButtonEventHandler
from System.Windows import MessageBox, MessageBoxButton, MessageBoxImage

class CellState:
    CLOSED = 0
    OPENED = 1
    FLAGGED = 2

class MinesweeperCell(object):
    def __init__(self, x, y, button):
        self.x = x
        self.y = y
        self.button = button
        self.is_mine = False
        self.state = CellState.CLOSED
        self.adjacent_mines = 0

class SettingsWindow(Window):
    def __init__(self):
        self.Title = u"Настройки сложности"
        self.Width = 350
        self.Height = 250
        self.WindowStartupLocation = System.Windows.WindowStartupLocation.CenterScreen
        self.ResizeMode = System.Windows.ResizeMode.NoResize
        self.Background = Brushes.WhiteSmoke

        panel = StackPanel()
        panel.Margin = Thickness(15)
        self.Content = panel

        panel.Children.Add(Label(Content=u"Ширина поля:"))
        self.width_input = TextBox(Text="9", Margin=Thickness(0,0,0,10))
        panel.Children.Add(self.width_input)

        panel.Children.Add(Label(Content=u"Высота поля:"))
        self.height_input = TextBox(Text="9", Margin=Thickness(0,0,0,10))
        panel.Children.Add(self.height_input)

        panel.Children.Add(Label(Content=u"Количество мин:"))
        self.mines_input = TextBox(Text="10", Margin=Thickness(0,0,0,10))
        panel.Children.Add(self.mines_input)

        self.start_btn = Button(Content=u"Начать игру")
        self.start_btn.Click += self.on_start_click
        panel.Children.Add(self.start_btn)

        self.result = None

    def on_start_click(self, sender, event):
        try:
            w = int(self.width_input.Text)
            h = int(self.height_input.Text)
            m = int(self.mines_input.Text)
            if w < 5 or w > 24 or h < 5 or h > 24:
                raise ValueError(u"Размер поля должен быть от 5 до 24")
            if m < 1 or m >= w*h:
                raise ValueError(u"Количество мин должно быть от 1 и меньше количества ячеек")
        except Exception as e:
            MessageBox.Show(unicode(e), u"Ошибка ввода", MessageBoxButton.OK, MessageBoxImage.Warning)
            return
        self.result = (w, h, m)
        self.Close()

class MinesweeperWindow(Window):
    def __init__(self, rows, cols, mines_count, icons_dir):
        self.rows = rows
        self.cols = cols
        self.mines_count = mines_count
        self.icons_dir = icons_dir

        self.Title = u"Serch bug in log Revit "
        self.Width = max(520, self.cols * 40)
        self.Height = max(580, self.rows * 45)
        self.MinWidth = 400
        self.MinHeight = 580
        self.Background = Brushes.WhiteSmoke

        self.icons = {}
        self.load_icons()

        self.cells = []

        self.flags_count = 0
        self.timer_started = False
        self.seconds_elapsed = 0
        self.best_time = None  # Лучший результат за сессию

        main_panel = System.Windows.Controls.DockPanel()
        self.Content = main_panel

        # Верхняя панель с изображением лица и лейблами
        top_panel = StackPanel()
        top_panel.Orientation = System.Windows.Controls.Orientation.Horizontal
        top_panel.HorizontalAlignment = HorizontalAlignment.Center
        top_panel.Margin = Thickness(5)
        System.Windows.Controls.DockPanel.SetDock(top_panel, System.Windows.Controls.Dock.Top)
        main_panel.Children.Add(top_panel)

        self.face_img = Image()
        self.face_img.Width = 40
        self.face_img.Height = 40
        self.face_img.Margin = Thickness(0, 0, 15, 0)
        self.face_img.Stretch = Stretch.Uniform
        top_panel.Children.Add(self.face_img)

        self.flags_label = Label()
        self.flags_label.Content = u"Мин осталось: {}".format(self.mines_count)
        self.flags_label.FontSize = 16
        self.flags_label.Margin = Thickness(10,0,10,0)
        top_panel.Children.Add(self.flags_label)

        self.timer_label = Label()
        self.timer_label.Content = u"Время: 0 с"
        self.timer_label.FontSize = 16
        self.timer_label.Margin = Thickness(10,0,10,0)
        top_panel.Children.Add(self.timer_label)

        self.best_time_label = Label()
        self.best_time_label.Content = u"Лучшее время: --"
        self.best_time_label.FontSize = 16
        self.best_time_label.Margin = Thickness(10,0,10,0)
        top_panel.Children.Add(self.best_time_label)

        # Нижняя панель с кнопками
        bottom_panel = StackPanel()
        bottom_panel.Orientation = System.Windows.Controls.Orientation.Horizontal
        bottom_panel.HorizontalAlignment = HorizontalAlignment.Center
        bottom_panel.Margin = Thickness(5)
        System.Windows.Controls.DockPanel.SetDock(bottom_panel, System.Windows.Controls.Dock.Bottom)
        main_panel.Children.Add(bottom_panel)

        self.settings_btn = Button()
        self.settings_btn.Content = u"Настройки"
        self.settings_btn.Margin = Thickness(10,0,10,0)
        self.settings_btn.Click += self.on_settings_click
        bottom_panel.Children.Add(self.settings_btn)

        self.restart_btn = Button()
        self.restart_btn.Content = u"Начать заново"
        self.restart_btn.Margin = Thickness(10,0,10,0)
        self.restart_btn.Click += self.on_restart_click
        bottom_panel.Children.Add(self.restart_btn)

        # Грид с ячейками
        self.grid = Grid()
        self.grid.HorizontalAlignment = HorizontalAlignment.Center
        self.grid.VerticalAlignment = VerticalAlignment.Center
        self.grid.Margin = Thickness(10)
        main_panel.Children.Add(self.grid)

        self.create_grid_definitions()

        # Таймер
        self.dispatcher_timer = System.Windows.Threading.DispatcherTimer()
        self.dispatcher_timer.Interval = System.TimeSpan.FromSeconds(1)
        self.dispatcher_timer.Tick += self.on_timer_tick

        self.init_cells()
        self.start_game()

    def create_grid_definitions(self):
        self.grid.RowDefinitions.Clear()
        self.grid.ColumnDefinitions.Clear()
        for _ in range(self.rows):
            self.grid.RowDefinitions.Add(System.Windows.Controls.RowDefinition())
        for _ in range(self.cols):
            self.grid.ColumnDefinitions.Add(System.Windows.Controls.ColumnDefinition())

    def load_icons(self):
        def load_icon(name):
            path = os.path.join(self.icons_dir, name)
            if not os.path.isfile(path):
                return None
            converter = ImageSourceConverter()
            return converter.ConvertFromString(path)

        self.icons['bomb'] = load_icon("bomb.png")
        self.icons['explosion'] = load_icon("explosion.png")
        self.icons['flag'] = load_icon("flag.png")
        self.icons['greed'] = load_icon("greed.png")
        self.icons['dead'] = load_icon("dead.png")
        self.icons['life'] = load_icon("life.png")

    def init_cells(self):
        self.cells = []
        self.grid.Children.Clear()
        self.flags_count = 0
        self.update_flags_label()

        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                btn = Button()
                btn.Margin = Thickness(0)
                btn.Padding = Thickness(0)
                btn.Background = Brushes.LightGray
                btn.HorizontalAlignment = HorizontalAlignment.Stretch
                btn.VerticalAlignment = VerticalAlignment.Stretch
                btn.Width = 35
                btn.Height = 35

                img = Image()
                img.Source = self.icons['greed']
                img.Stretch = Stretch.Uniform
                btn.Content = img

                btn.PreviewMouseLeftButtonUp += MouseButtonEventHandler(self.on_left_click)
                btn.PreviewMouseRightButtonUp += MouseButtonEventHandler(self.on_right_click)

                System.Windows.Controls.Grid.SetRow(btn, r)
                System.Windows.Controls.Grid.SetColumn(btn, c)
                self.grid.Children.Add(btn)

                cell = MinesweeperCell(r, c, btn)
                row_cells.append(cell)
            self.cells.append(row_cells)

    def start_game(self):
        self.timer_started = False
        self.seconds_elapsed = 0
        self.update_timer_label()
        self.dispatcher_timer.Stop()

        self.flags_count = 0
        self.update_flags_label()

        for row in self.cells:
            for cell in row:
                cell.is_mine = False
                cell.state = CellState.CLOSED
                cell.adjacent_mines = 0
                self.set_cell_image(cell, 'greed')
                cell.button.IsEnabled = True
                cell.button.Content = Image(Source=self.icons['greed'], Stretch=Stretch.Uniform, Width=25, Height=25)

        mines_placed = 0
        while mines_placed < self.mines_count:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            cell = self.cells[r][c]
            if not cell.is_mine:
                cell.is_mine = True
                mines_placed += 1

        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[r][c]
                if cell.is_mine:
                    continue
                count = 0
                for nr in range(max(0, r-1), min(self.rows, r+2)):
                    for nc in range(max(0, c-1), min(self.cols, c+2)):
                        if self.cells[nr][nc].is_mine:
                            count += 1
                cell.adjacent_mines = count

        self.face_img.Source = self.icons['life']

    def update_flags_label(self):
        mines_left = self.mines_count - self.flags_count
        if mines_left < 0:
            mines_left = 0
        self.flags_label.Content = u"Мин осталось: {}".format(mines_left)

    def update_timer_label(self):
        self.timer_label.Content = u"Время: {} с".format(self.seconds_elapsed)

    def update_best_time_label(self):
        if self.best_time is None:
            self.best_time_label.Content = u"Лучшее время: --"
        else:
            self.best_time_label.Content = u"Лучшее время: {} с".format(self.best_time)

    def on_timer_tick(self, sender, event):
        self.seconds_elapsed += 1
        self.update_timer_label()

    def on_restart_click(self, sender, event):
        self.start_game()

    def on_settings_click(self, sender, event):
        settings = SettingsWindow()
        settings.ShowDialog()
        if settings.result is None:
            return
        self.rows, self.cols, self.mines_count = settings.result
        self.Width = max(520, self.cols * 40)
        self.Height = max(580, self.rows * 45)
        self.create_grid_definitions()
        self.init_cells()
        self.start_game()
        self.update_best_time_label()

    def on_left_click(self, sender, event):
        if not self.timer_started:
            self.timer_started = True
            self.dispatcher_timer.Start()

        for row in self.cells:
            for cell in row:
                if cell.button == sender:
                    if cell.state == CellState.CLOSED:
                        self.open_cell(cell)
                    return

    def on_right_click(self, sender, event):
        for row in self.cells:
            for cell in row:
                if cell.button == sender:
                    if cell.state == CellState.CLOSED:
                        cell.state = CellState.FLAGGED
                        self.flags_count += 1
                        self.set_cell_image(cell, 'flag')
                    elif cell.state == CellState.FLAGGED:
                        cell.state = CellState.CLOSED
                        self.flags_count -= 1
                        self.set_cell_image(cell, 'greed')
                    self.update_flags_label()
                    return

    def open_cell(self, cell):
        if cell.state != CellState.CLOSED:
            return
        if cell.is_mine:
            self.set_cell_image(cell, 'explosion')
            self.game_over()
            return

        cell.state = CellState.OPENED
        if cell.adjacent_mines == 0:
            self.set_cell_image(cell, None)
            for nr in range(max(0, cell.x-1), min(self.rows, cell.x+2)):
                for nc in range(max(0, cell.y-1), min(self.cols, cell.y+2)):
                    if nr == cell.x and nc == cell.y:
                        continue
                    self.open_cell(self.cells[nr][nc])
        else:
            num_lbl = self.make_number_label(cell.adjacent_mines)
            cell.button.Content = num_lbl

        if self.check_win():
            self.on_win()

    def on_win(self):
        self.dispatcher_timer.Stop()
        self.disable_all_buttons()
        if self.best_time is None or self.seconds_elapsed < self.best_time:
            self.best_time = self.seconds_elapsed
        self.update_best_time_label()
        self.show_result(u"Поздравляем! Вы выиграли!")

    def make_number_label(self, number):
        lbl = Label()
        lbl.Content = str(number)
        lbl.FontSize = 20
        lbl.FontWeight = System.Windows.FontWeights.Bold
        lbl.HorizontalContentAlignment = HorizontalAlignment.Center
        lbl.VerticalContentAlignment = VerticalAlignment.Center
        lbl.Foreground = Brushes.Blue
        lbl.Width = 35
        lbl.Height = 35
        return lbl

    def set_cell_image(self, cell, icon_name):
        if icon_name is None:
            cell.button.Content = None
            cell.button.Background = Brushes.White
        else:
            img = Image()
            img.Source = self.icons.get(icon_name, None)
            img.Stretch = Stretch.Uniform
            img.Width = 25
            img.Height = 25
            cell.button.Content = img
            cell.button.Background = Brushes.LightGray

    def game_over(self):
        self.dispatcher_timer.Stop()
        self.face_img.Source = self.icons['dead']
        self.disable_all_buttons()
        for row in self.cells:
            for cell in row:
                if cell.is_mine and cell.state != CellState.FLAGGED:
                    self.set_cell_image(cell, 'bomb')
        self.show_result(u"Вы проиграли!")

    def disable_all_buttons(self):
        for row in self.cells:
            for cell in row:
                cell.button.IsEnabled = False

    def check_win(self):
        for row in self.cells:
            for cell in row:
                if not cell.is_mine and cell.state != CellState.OPENED:
                    return False
        return True

    def show_result(self, message):
        result = MessageBox.Show(message + u"\nХотите начать заново?", u"Результат игры",
                                 MessageBoxButton.YesNo, MessageBoxImage.Information)
        if result == System.Windows.MessageBoxResult.Yes:
            self.start_game()
            self.seconds_elapsed = 0
            self.update_timer_label()
            self.dispatcher_timer.Start()
        else:
            self.Close()

def run():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, "icons")

    settings = SettingsWindow()
    settings.ShowDialog()

    if settings.result is None:
        return

    w, h, m = settings.result
    win = MinesweeperWindow(w, h, m, icons_dir)
    win.ShowDialog()

if __name__ == "__main__":
    run()
