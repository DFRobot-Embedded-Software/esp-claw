/*
 * DFRobot K10 board-specific factory entries for ESP Board Manager.
 */

#include <stdlib.h>
#include "esp_log.h"
#include "esp_io_expander_tca95xx_16bit.h"
#include "esp_lcd_ili9341.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_board_device.h"
#include "button_interface.h"
#include "dev_button.h"

/* Buttons on the TCA9555 expander, active-low.
 * Keep in sync with custom_io metadata in board_devices.yaml. */
#define K10_BUTTON_KB_PIN  2   /* XL9555 P02 */
#define K10_BUTTON_KA_PIN  12  /* XL9555 P14 = port1 bit4 */

static const char *TAG = "DFROBOT_K10_SETUP_DEVICE";

esp_err_t io_expander_factory_entry_t(i2c_master_bus_handle_t i2c_handle, const uint16_t dev_addr, esp_io_expander_handle_t *handle_ret)
{
    esp_err_t ret = esp_io_expander_new_i2c_tca95xx_16bit(i2c_handle, dev_addr, handle_ret);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create TCA95xx IO expander handle: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Match original df-k10 power-up/reset sequence:
     * drive P0/P1 low briefly, then high, then leave inputs for keys handled by board manager.
     */
    const uint32_t reset_mask = IO_EXPANDER_PIN_NUM_0 | IO_EXPANDER_PIN_NUM_1;
    ret = esp_io_expander_set_dir(*handle_ret, reset_mask, IO_EXPANDER_OUTPUT);
    if (ret == ESP_OK) {
        ret = esp_io_expander_set_level(*handle_ret, reset_mask, 0);
    }
    if (ret == ESP_OK) {
        vTaskDelay(pdMS_TO_TICKS(100));
        ret = esp_io_expander_set_level(*handle_ret, reset_mask, 1);
    }
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "IO expander reset sequence failed: %s", esp_err_to_name(ret));
    }
    return ret;
}

esp_err_t lcd_panel_factory_entry_t(esp_lcd_panel_io_handle_t io, const esp_lcd_panel_dev_config_t *panel_dev_config, esp_lcd_panel_handle_t *ret_panel)
{
    esp_err_t ret = esp_lcd_new_panel_ili9341(io, panel_dev_config, ret_panel);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create ILI9341 panel handle: %s", esp_err_to_name(ret));
    }
    return ret;
}

/* --- KB / KA custom button drivers (iot_button over the IO expander) --- */

typedef struct {
    button_driver_t          base;
    uint16_t                 pin_num;
    uint8_t                  active_level;
    esp_io_expander_handle_t io_handle;
} k10_button_driver_t;

static uint8_t k10_button_get_level(button_driver_t *driver)
{
    k10_button_driver_t *btn = (k10_button_driver_t *)driver;
    if (!btn->io_handle) {
        return 0;
    }
    uint32_t level = 0;
    uint32_t pin_mask = (1U << btn->pin_num);
    if (esp_io_expander_get_level(btn->io_handle, pin_mask, &level) != ESP_OK) {
        return 0;
    }
    return (!!(level & pin_mask) == btn->active_level);
}

static esp_err_t k10_button_del(button_driver_t *driver)
{
    free(driver);
    return ESP_OK;
}

static button_driver_t *k10_button_create(uint16_t pin_num, const char *name)
{
    esp_io_expander_handle_t *exp_ptr = NULL;
    if (esp_board_device_get_handle("gpio_expander", (void **)&exp_ptr) != ESP_OK ||
        exp_ptr == NULL || *exp_ptr == NULL) {
        ESP_LOGE(TAG, "Failed to get gpio_expander handle for %s", name);
        return NULL;
    }

    k10_button_driver_t *btn = calloc(1, sizeof(k10_button_driver_t));
    if (!btn) {
        ESP_LOGE(TAG, "Failed to allocate button driver for %s", name);
        return NULL;
    }
    btn->io_handle = *exp_ptr;
    btn->pin_num = pin_num;
    btn->active_level = 0;  /* active-low */
    btn->base.get_key_level = k10_button_get_level;
    btn->base.del = k10_button_del;
    btn->base.enable_power_save = false;
    return &btn->base;
}

static button_driver_t *button_kb(const dev_button_config_t *config)
{
    (void)config;
    return k10_button_create(K10_BUTTON_KB_PIN, "button_kb");
}

static button_driver_t *button_ka(const dev_button_config_t *config)
{
    (void)config;
    return k10_button_create(K10_BUTTON_KA_PIN, "button_ka");
}

DEVICE_EXTRA_FUNC_REGISTER(button_kb, button_kb);
DEVICE_EXTRA_FUNC_REGISTER(button_ka, button_ka);
