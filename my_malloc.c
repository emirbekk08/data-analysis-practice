#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>

// Структура скрытого заголовка для каждого блока памяти
struct BlockHeader {
    size_t size;               // Размер полезной памяти в байтах
    int is_free;               // 1 = блок свободен, 0 = блок занят
    struct BlockHeader* next;  // Указатель на следующий блок
};

// Глобальный указатель на начало нашей памяти
static struct BlockHeader* first_block = NULL;

// Выделяем регион размером 64 Килобайта для тестов
#define REGION_SIZE (64 * 1024)

// Инициализация памяти через один регион mmap()
void init_memory() {
    void* heap_start = mmap(NULL, REGION_SIZE, PROT_READ | PROT_WRITE, 
                            MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);
    
    if (heap_start == MAP_FAILED) {
        perror("mmap failed");
        exit(1);
    }

    first_block = (struct BlockHeader*)heap_start;
    first_block->size = REGION_SIZE - sizeof(struct BlockHeader);
    first_block->is_free = 1;
    first_block->next = NULL;
}

// Наш аллокатор памяти (Стратегия First Fit с разбиением блоков)
void* my_malloc(size_t size) {
    if (first_block == NULL) {
        init_memory();
    }

    struct BlockHeader* current = first_block;

    // Шаг 1. Ищем первый свободный блок подходящего размера
    while (current != NULL) {
        if (current->is_free && current->size >= size) {
            
            // Шаг 2. Разбиение блока (Splitting), если остаток достаточно большой
            // Нам нужно место как минимум под еще один заголовок BlockHeader + хотя бы 1 байт данных
            if (current->size >= size + sizeof(struct BlockHeader) + 1) {
                // Вычисляем адрес нового заголовка для остатка свободной памяти
                struct BlockHeader* next_free_block = (struct BlockHeader*)((char*)current + sizeof(struct BlockHeader) + size);
                
                // Настраиваем параметры нового свободного блока
                next_free_block->size = current->size - size - sizeof(struct BlockHeader);
                next_free_block->is_free = 1;
                next_free_block->next = current->next;
                
                // Перестраиваем текущий блок под размер запроса
                current->size = size;
                current->next = next_free_block;
            }

            // Помечаем блок как занятый
            current->is_free = 0;

            // Возвращаем пользователю указатель на память СРАЗУ ПОСЛЕ заголовка
            return (void*)((char*)current + sizeof(struct BlockHeader));
        }
        current = current->next;
    }

    // Если свободной памяти нужного размера не нашлось
    return NULL; 
}

// Функция освобождения памяти со слиянием свободных дыр (Coalescing)
void my_free(void* ptr) {
    if (ptr == NULL) return;

    // Вычисляем адрес заголовка, сдвигая указатель пользователя назад
    struct BlockHeader* block = (struct BlockHeader*)((char*)ptr - sizeof(struct BlockHeader));
    block->is_free = 1; // Освобождаем блок

    // Шаг 3. Слияние (Coalescing) соседних свободных дыр за один проход
    struct BlockHeader* current = first_block;
    while (current != NULL && current->next != NULL) {
        if (current->is_free && current->next->is_free) {
            // Склеиваем текущий блок со следующим: суммируем их размеры + размер поглощенного заголовка
            current->size += sizeof(struct BlockHeader) + current->next->size;
            current->next = current->next->next; // Выбрасываем поглощенный заголовок из списка
        } else {
            current = current->next;
        }
    }
}

// Демонстрационный запуск для проверки работоспособности
int main() {
    printf("--- Тестирование кастомного аллокатора памяти на Си ---\n");

    // Выделяем три блока
    int* p1 = (int*)my_malloc(100 * sizeof(int));
    int* p2 = (int*)my_malloc(200 * sizeof(int));
    int* p3 = (int*)my_malloc(50 * sizeof(int));

    if (p1 && p2 && p3) {
        printf("Успешно выделили 3 блока памяти поверх mmap регионов!\n");
        
        p1[0] = 42;
        p2[0] = 100;
        printf("Проверка записи данных: p1[0] = %d, p2[0] = %d\n", p1[0], p2[0]);
    }

    // Освобождаем память
    my_free(p2);
    printf("Блок p2 успешно освобожден. Соседние дыры готовы к слиянию.\n");
    
    my_free(p1);
    my_free(p3);

    printf("Вся память очищена. Аллокатор отработал успешно!\n");
    return 0;
}
