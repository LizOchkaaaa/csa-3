# Лабораторная работа №3 по Архитектуре Компьютера

- Суворова Елизавета Михайловна. P3223
- `forth | stack | harv | mc | tick | struct | stream | mem | cstr | prob1`
- Базовый вариант

## Оглавление
1. [Язык программирования](#lang)
2. [Организация памяти](#memory)
3. [Машинные инструкции](#instructions)
4. [Транслятор](#translator)
5. [Модель процессора](#processor)
6. [Тестирование](#testing)
7. [CI](#ci)
8. [Аналитика алгоритмов](#alg)

## Язык программирования - Forth <a id='lang'></a>
```
program ::= { string }

string ::= { <any of [ term ]> } "\n"
       | { <any of [ term ] [ comment ]> } "\n"

term ::= oper
       | integer
       | out_string
       | variable

oper ::= "dup"
       | "drop"
       | "clear"
       | "cr"
       | "key"
       | "."
       | "if"
       | "else"
       | "begin"
       | "until"
       | ":"
       | ";"
       | + | - | * | / | mod | ++ | -- | <= | > | = | != | ++ | --

integer ::= [ "-" ] { <any of "0-9"> }
   
out_string ::= "."{ <any symbols except '"'> }
      
variable ::= <any of "a-z A-Z 0-9 _">
      | <any of "a-z A-Z 0-9 _"> !
      | <any of "a-z A-Z 0-9 _"> !*
      | <any of "a-z A-Z 0-9 _"> @
      | <any of "a-z A-Z 0-9 _"> @*

comment ::= "/"<any symbols>"/"
```
**Лексемы:**

Язык Forth состоит из лексем, которые отделяются друг от друга пробелами или переносами строк. Лексемы описаны 
в классе `Term` в файле [isa.py](https://github.com/LizOchkaaaa/csa-3/blob/master/processor/isa.py).

- `[Любое целое число]` - добавить в стек данных данное число
- `dup` - продублировать в стек данных число из TOS
- `drop` - записать в tos верхнее число из стека данных (удалить число из стека)
- `clear` - очистить стек данных
- `emit` - напечатать символ, код которого лежит в TOS
- `cr` - напечатать символ переноса строки (код 10)
- `key` - получить код символа из буфера ввода (из ячейки памяти, которая настроена на вывод)
- `.` - вывести значение из вершины стека
- `."string"` - вывести строку, указанную в кавычках после точки
- `if / else` - условие. Код, написанный после if и до символа ";" или else будет выполняться, если в TOS лежит
"1", иначе будет выполняться код, написанный после else и до символа ";".
- `;` - окончание условного кода
- `begin` - начало цикла
- `until` - окончание цикла. Будет осуществлен возврат к первому лексему внутри цикла, если в TOS "1".
- `:` - объявление и окончание процедуры
- `[название переменной или процедуры]` - если это процедура, то название процедуры должно идти после двоеточий.
Если это переменная, то после названия должен идти один из следующих лексем: "!, @, !\*, @\*"
- `!` - сохранить в переменную значение в TOS
- `@` - записать в TOS значение из переменной
- `!*` - сохранить значение TOS в ячейку памяти, адрес которой лежит в памяти, на которую указывает переменная.
- `@*` - записать в TOS значение из ячейки памяти, адрес которой лежит в памяти, на которую указывает переменная.
- `+ | - | * | / | mod` - сложить/вычесть/умножить/разделить/найти остаток от деления TOS на вершину стека данных.
- `<= | > | = | !=` - положить на вершину стека "1", если выполняется условие между TOS и вершиной стека данных
меньше либо равно/больше/равно/не равно.
- `++ | --` - инкремент/декремент TOS

**Соответствующие машинные инструкции**

Практически все лексемы однозначно транслируются в соответствующие им машинные инструкции

| Лексема | Инструкция |                Аргумент                 | Кол-во тактов |
|---------|------------|:---------------------------------------:|:-------------:|
| [Число] | push       |              Данное число               |       3       |
| dup     | dup        |               Отсутствует               |       2       | 
| drop    | drop       |               Отсутствует               |       3       |
| clear   | clear      |               Отсутствует               |       2       |
| emit    | store      |        Ячейка памяти вывода (1)         |       3       | 
| key     | load       |        Ячейка памяти вывода (0)         |       3       |
| .       | store      |        Ячейка памяти вывода (1)         |       3       |
| if      | jif        | адрес инструкции за пределами кода в if |       1       |
| else    | jmp        |  адрес инструкции за пределами if else  |       1       |
| until   | jif        |  адрес первой инструкции в блоке цикла  |       1       |
| !       | store      | ячейка, на которую указывает переменная |       3       |
| @       | load       | ячейка, на которую указывает переменная |       3       |
| !*      | ind_store  | ячейка, на которую указывает переменная |       5       |
| @*      | ind_load   | ячейка, на которую указывает переменная |       6       |
| +       | add        |               Отсутствует               |       4       |
| -       | sub        |               Отсутствует               |       4       |
| *       | mul        |               Отсутствует               |       4       |
| /       | div        |               Отсутствует               |       4       |
| mod     | mod        |               Отсутствует               |       4       |
| <=      | less_eq    |               Отсутствует               |       4       |
| \>      | greater    |               Отсутствует               |       4       |
| =       | equal      |               Отсутствует               |       4       |
| !=      | n_equal    |               Отсутствует               |       4       |
| ++      | inc        |               Отсутствует               |       3       |
| --      | dec        |               Отсутствует               |       3       |

- `cr` транслируется в 3 инструкции: push (10), store (OUTPUT_ADDRESS), drop. То есть в TOS добавляется код операции
переноса строки - 10, затем он записывается в ячейку памяти вывода, в конце число 10 удаляется из стека. Всего 7 тактов.
- <a id='string'></a>Операция вывода строки `."string"` транслируется в dup, top (char), store (OUTPUT_ADDRESS), ..., drop. 
Количество инструкций top и store зависит от длины строки. Инструкция top изменяет TOS кодом символа из строки.
Количество тактов данной операции составляет от 4 до 4 + (2n - 1) , где n - длина строки.
- Математические операции, а также операции dup, key и добавление числа в TOS изменяет глубину стека. То есть
перед тем, как изменить значение TOS, оно добавляется на вершину стека данных. Однако операции инкремента и декремента,
а также машинная инструкция top изменяет значение TOS, не добавляя его в стек данных. Реализовано с целью уменьшения
количества машинных инструкций.
- В конце программы добавляется инструкция stop, которая останавливает процессор.

## Организация памяти <a id='memory'></a>

Модель памяти процессора:
1. Память команд и данных разделены (Гарвардская архитектура)
2. Память команд. Машинное слово - не определено. Реализуется списком словарей, описывающих инструкции 
(одно слово - одна ячейка).
3. Память данных. Ячейка памяти - 4 байта, знаковое. Реализуется списком чисел.
4. Стек данных. Заменяет регистры (стековая архитектура). Ограничения на размер стека нет.
5. Все вычисления происходят вокруг TOS (Top Of the Stack) - 4 байта. Для математической операции используются 
значение из TOS и значение из верхней ячейки стека данных.

```
TOS
+--------------+
|    value     |
+--------------+

 Data Stack
+------------------------------+
| 00  : value                  |
| 01  : value                  |
|             ...              |
| n   : value                  |
+------------------------------+

 Instruction memory
+------------------------------+
| 00  : instruction (start)    |
| 01  : instruction            |
|             ...              |
| n   : instruction (end)      |
+------------------------------+

 Instruction mc_memory
+------------------------------+
| 00  : mc_instruction         |
| 01  : mc_instruction         |
|             ...              |
| n   : mc_instruction         |
+------------------------------+

  Data memory
+------------------------------+
| 00  : value/in               |
| 01  : variable/out           |
|    ...                       |
| n   : variable               |
+------------------------------+

```

**Типы адресации**

- Прямая загрузка. Загрузка значения аргумента инструкции напрямую в TOS. Например, push 30, top 30 - обе инструкции
изменяют значения стека на число 30.
- Абсолютная адресация. Такая адресация используется только в инструкциях load и store. То есть инструкция load 5
загружает значение TOS в ячейку памяти 5. В Forth для сохранения в память используется символ `!`, а для загрузки
символ `@`.
- Косвенная адресация. Такая адресация используется только в инструкциях ind_load и ind_store. То есть инструкция
ind_load 5. Загрузит в TOS значение из ячейки памяти, адрес которой указан в ячейки памяти 5. В Forth для 
косвенного сохранения в память используется символ `!*`, а для косвенной загрузки символ `@*`.

**Машинные инструкции** <a id='instructions'></a>

- Машинный код сериализуется в список JSON.
- Один элемент списка - одна инструкция.
- Индекс списка - адрес инструкции. Используется для прыжков на определенные инструкции.
```
 [{
    "index": 0, 
    "term": 4
    "opcode": "push", 
    "arg": "4"
 }]
```
- index - адрес инструкции в памяти инструкций
- term - лексема на языке Forth
- opcode - машинная инструкция;
- arg - аргумент (может отсутствовать);

## Транслятор <a id='translator'></a>

Интерфейс командной строки: translator.py <input_file> <target_file>

Файл: [translator.py](https://github.com/LizOchkaaaa/csa-3/blob/master/translator.png)

Алгоритм трансляции:
1. Разбиваю код на лексемы по пробелам и по переносам строк.
2. Если строка содержит комментарий, перехожу к следующей строке.
3. Перевожу в машинный код лексемы языка Forth, которые однозначно транслируются в машинный код, например dup,
drop, clear, число и тд.
4. Конструкция if else транслируется в следующую схему:
    - проверяется инвертированное условие. Если оно верное, то значит прыгаем в часть машинного кода, где реализован
    else. Если условие неверное, то переходим на следующую инструкцию, где реализованы инструкции внутри if.
    В конце if располагается инструкция безусловного прыжка `jmp`, которая перепрыгивает блок else. Если else
    отсутствует, то `jmp` тоже отсутствует.
    - Так как в начале блока if мы не знаем, куда перепрыгивать, если инвертированное условие выполняется, то мы
   добавляем в буфер прыжков адрес команды `jif`, а по окончанию блока подставляю аргумент для этой инструкции.
   То же самое и для `jmp`, если присутствует else. 
5. Конструкция цикла begin until транслируется как:
    - когда встретился `begin` в буфер добавляется адрес первой инструкции в цикле.
    - конец цикла `until` транслируется в инструкцию `jif`, которая совершает прыжок на сохраненную в буфере прыжков
    первую инструкцию в цикле
6. Вывод строки `."string"` транслируется в последовательность инструкций, которые описаны [выше](#string).
7. Код в процедурах транслируется, как обычно, но по окончании процедуры он удаляется из основного машинного кода
и добавляется в словарь процедур. Когда процедура встречается в коде, вместо названия процедуры подставляется этот
код.
8. В конце машинного кода вставляется инструкция `stop`.

## Модель процессора <a id='processor'></a>

Интерфейс командной строки: simulation.py <machine_code_file> <input_file>

### ControlUnit

![control_unit](https://github.com/LizOchkaaaa/csa-3/blob/master/readme/schemes/control_unit.png)

Реализован в классе `ControlUnit` в [machine.py](https://github.com/LizOchkaaaa/csa-3/blob/master/processor/machine.py).

Microcode
- Память микрокоманд хранится в виде списка в [microcode.py](https://github.com/LizOchkaaaa/csa-3/blob/master/processor/microcode.py)
Hardwired (реализовано полностью на Python).
- Каждый элемент списка представляет собой список, составленный из ссылок на функции и их аргументы, имитирующих сигналы
процессора.
- Если функция содержит аргументы, то ссылка на функцию и аргументы заключаются в кортеж.
- Вся память микроинструкций поделена на инструкции. Инструкции могут содержать разное количество микроинструкций.
    - В начале исполнения каждой инструкции ее операционный код переводится в адрес нужной минкроинструкции, где
    находится исполнение этой самой инструкции. Затем совершается прыжок на этот адрес. Данная микроинстр. лежит по адресу 0.
    - Далее идет выполнение этих микроинструкций. Почти в каждой микроинстр. закодирован сигнал перехода на сле
    дующую микроинстр.
    - Практически в конце каждой инструкции (кроме stop, jmp и jif) находится микроинстр. перехода на следующую
    инструкцию в памяти инструкций и прыжок на нулевой адрес, откуда происходит снова трансляцию из операционного кода
    в адрес нужной микроинструкции.
- Исполнение микроинструкций и вся симуляция в целом происходит в методе ```start```.
- Указатель на текущую инструкцию лежит в `PC`, а указатель на текущую микроинструкцию лежит в `mPC`.


- Отсчет времени работы ведется в тактах.
- После каждого такта выводится информация о состоянии процессора. Состояние процессора показывает:
    - текущий терм на языке Forth и текущую инструкцию
    - текущий такт
    - значения TOS и стек данных
    - данные на шинах (alu_out и data_memory_out)
    - значения в PC и mPC
- В целях уменьшения размера golden тестов происходит срез лога после 700 такта.

**Сигналы**
- `sel_pc` - выбирается адрес следующий команды.
- `jmp_type` - выбирается тип перехода на следующую инструкцию. Если выполняется инструкция `jif`, то пропускается
сигнал по линии `tos (bool)`, в остальных случаях пропускается сигнал `sel_pc`, идущий из `mProgram`.
- `sel_mPC` - выборка следующей микроинструкции.

### DataPath

![DataPath](https://github.com/LizOchkaaaa/csa-3/blob/master/readme/schemes/data_path.py)

Реализован в классе `DataPath` в [machine.py](https://github.com/LizOchkaaaa/csa-3/blob/master/processor/machine.py).

- Управляющие сигналы и поступают с памяти микрокоманд `mProgram`.

**Сигналы**

- `ds_push` - Записать на вершину стека данных значение из tos
- `ds_pop` -удалить верхний элемент из стека данных.
- `ds_clear` - очистить стек данных, не включая TOS.
- `latch_tos` - выбрать одну из шин (аргумент инструкции, данные с АЛУ, данные из памяти или верхний элемент стека) и
записать данные на этой шине в TOS
- `latch_address` - выбрать одну из шин (аргумент инструкции или данные из памяти).
- `operation` - выбор математической операции для АЛУ.
- `read/write` - сигналы для чтения и записи данных в память соответственно.

Данные, прошедшие через АЛУ выставляются на шину `alu_out`, а данные, прочитанные из памяти, на `data_mem_out`.

Флаги в процессоре отсутствуют. Для условных переходов используется значение TOS. Если в TOS не 0, то совершается
прыжок в инструкции `jif`, иначе значение в `PC` инкриминируется.

## Тестирование <a id='testing'></a>

Тестирование выполняется при помощи golden test-ов в формате yaml с использованием библиотеки `pytest`. Файлы .yml лежат в папке 
[tests](https://github.com/LizOchkaaaa/csa-3/blob/master/tests). Тесты содержат
1. входные данные
2. код программы
3. машинный код
4. вывод процессора
5. журнал работы процессора

Результат golden_test:

```
golden_test.py::test_golden[tests/cat_golden.yml] PASSED                                                                                                                         [ 25%]
golden_test.py::test_golden[tests/hello_golden.yml] PASSED                                                                                                                       [ 50%]
golden_test.py::test_golden[tests/hello_user_name_golden.yml] PASSED                                                                                                             [ 75%]
golden_test.py::test_golden[tests/prob1_golden.yml] PASSED  
       
```

Пример алгоритма [cat.fr](https://github.com/LizOchkaaaa/csa-3/blob/master/resources/forth/cat.fr)
- Ввод: `cat cat cat`

  - Вывод:
      ```
      DEBUG: (0: clear -> clear ) - TICK: 0 - TOS: 0 - data stack: [] - alu out: 0 - memory out: 0 - address reg: 0 - PC: 0 - mPC: 10
      DEBUG: (0: clear -> clear ) - TICK: 1 - TOS: 0 - data stack: [] - alu out: 0 - memory out: 0 - address reg: 0 - PC: 0 - mPC: 11
      DEBUG: (1: key -> load 0) - TICK: 2 - TOS: 0 - data stack: [] - alu out: 0 - memory out: 0 - address reg: 0 - PC: 1 - mPC: 0
      DEBUG: (1: key -> load 0) - TICK: 3 - TOS: 0 - data stack: [] - alu out: 0 - memory out: 0 - address reg: 0 - PC: 1 - mPC: 12
      DEBUG: (1: key -> load 0) - TICK: 4 - TOS: 0 - data stack: [] - alu out: 0 - memory out: 0 - address reg: 0 - PC: 1 - mPC: 13
      INFO: add char 'c' from input buffer
      DEBUG: (1: key -> load 0) - TICK: 5 - TOS: 99 - data stack: [0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 1 - mPC: 14
      DEBUG: (2: 0 -> push 0) - TICK: 6 - TOS: 99 - data stack: [0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 2 - mPC: 0
      DEBUG: (2: 0 -> push 0) - TICK: 7 - TOS: 99 - data stack: [0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 2 - mPC: 6
      DEBUG: (2: 0 -> push 0) - TICK: 8 - TOS: 0 - data stack: [0, 99] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 2 - mPC: 7
      DEBUG: (3: != -> equal ) - TICK: 9 - TOS: 0 - data stack: [0, 99] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 3 - mPC: 0
      DEBUG: (3: != -> equal ) - TICK: 10 - TOS: 0 - data stack: [0, 99] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 3 - mPC: 56
      DEBUG: (3: != -> equal ) - TICK: 11 - TOS: 0 - data stack: [0, 99] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 3 - mPC: 57
      DEBUG: (3: != -> equal ) - TICK: 12 - TOS: 0 - data stack: [0, 99, 0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 3 - mPC: 58
      DEBUG: (3: != -> equal ) - TICK: 13 - TOS: 0 - data stack: [0, 99, 0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 3 - mPC: 59
      DEBUG: (4: if -> jif 9) - TICK: 14 - TOS: 0 - data stack: [0, 99, 0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 4 - mPC: 0
      DEBUG: (4: if -> jif 9) - TICK: 15 - TOS: 0 - data stack: [0, 99, 0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 4 - mPC: 69
      DEBUG: (5: drop -> drop ) - TICK: 16 - TOS: 0 - data stack: [0, 99, 0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 5 - mPC: 0
      DEBUG: (5: drop -> drop ) - TICK: 17 - TOS: 0 - data stack: [0, 99, 0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 5 - mPC: 3
      DEBUG: (5: drop -> drop ) - TICK: 18 - TOS: 0 - data stack: [0, 99, 0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 5 - mPC: 4
      DEBUG: (5: drop -> drop ) - TICK: 19 - TOS: 0 - data stack: [0, 99] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 5 - mPC: 5
      DEBUG: (6: drop -> drop ) - TICK: 20 - TOS: 0 - data stack: [0, 99] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 6 - mPC: 0
      DEBUG: (6: drop -> drop ) - TICK: 21 - TOS: 0 - data stack: [0, 99] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 6 - mPC: 3
      DEBUG: (6: drop -> drop ) - TICK: 22 - TOS: 99 - data stack: [0, 99] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 6 - mPC: 4
      DEBUG: (6: drop -> drop ) - TICK: 23 - TOS: 99 - data stack: [0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 6 - mPC: 5
      DEBUG: (7: emit -> store 1) - TICK: 24 - TOS: 99 - data stack: [0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 7 - mPC: 0
      DEBUG: (7: emit -> store 1) - TICK: 25 - TOS: 99 - data stack: [0] - alu out: 0 - memory out: 99 - address reg: 0 - PC: 7 - mPC: 20
      DEBUG: (7: emit -> store 1) - TICK: 26 - TOS: 99 - data stack: [0] - alu out: 0 - memory out: 99 - address reg: 1 - PC: 7 - mPC: 21
      INFO: add char 'c' to output buffer
    
      ...
  
      DEBUG: (13: None -> stop ) - TICK: 483 - TOS: 0 - data stack: [1, 0, 0, 0] - alu out: 0 - memory out: 0 - address reg: 0 - PC: 13 - mPC: 70
      cat cat cat 
      -------------------------------
      Количество инструкций: 14
      Количество тактов: 484
      ```

Основной файл с кодом теста находится в [golden_asm_test.py](https://github.com/LizOchkaaaa/csa-3/blob/master/golden_test.py)

### CI <a id='ci'></a>

Настройка CI находится в файле [.github/ci.yml](https://github.com/LizOchkaaaa/csa-3/blob/master/.github/workflows/ci.yml)

Тесты запускаются командой `pytest`. Линтер запускается командой `ruff check`.


## Аналитика алгоритмов <a id='alg'></a>

```
| Суворова Е.М. | hello | 1 | 27 | 27 | 93 | (forth | stack | harv | mc | tick | struct | stream | mem | cstr | prob1)
| Суворова Е.М. | cat | 6 | 14 | 142 | 484 | (forth | stack | harv | mc | tick | struct | stream | mem | cstr | prob1)
| Суворова Е.М. | hello user name | 23 | 90 | 174 | 633 | (forth | stack | harv | mc | tick | struct | stream | mem | cstr | prob1)
```
