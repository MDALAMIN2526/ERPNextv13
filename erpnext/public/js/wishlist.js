frappe.provide("erpnext.wishlist");
var wishlist = erpnext.wishlist;

frappe.provide("erpnext.shopping_cart");
var shopping_cart = erpnext.shopping_cart;

$.extend(wishlist, {
	set_wishlist_count: function() {
		// set badge count for wishlist icon
		var wish_count = frappe.get_cookie("wish_count");
		if (frappe.session.user==="Guest") {
			wish_count = 0;
		}

		if (wish_count) {
			$(".wishlist").toggleClass('hidden', false);
		}

		var $wishlist = $('.wishlist-icon');
		var $badge = $wishlist.find("#wish-count");

		if (parseInt(wish_count) === 0 || wish_count === undefined) {
			$wishlist.css("display", "none");
		} else {
			$wishlist.css("display", "inline");
		}
		if (wish_count) {
			$badge.html(wish_count);
			$wishlist.addClass('cart-animate');
			setTimeout(() => {
				$wishlist.removeClass('cart-animate');
			}, 500);
		} else {
			$badge.remove();
		}
	},

	bind_move_to_cart_action: function() {
		// move item to cart from wishlist
		$('.page_content').on("click", ".btn-add-to-cart", (e) => {
			const $move_to_cart_btn = $(e.currentTarget);
			let item_code = $move_to_cart_btn.data("item-code");

			shopping_cart.shopping_cart_update({
				item_code,
				qty: 1,
				cart_dropdown: true
			});

			let success_action = function() {
				const $card_wrapper = $move_to_cart_btn.closest(".wishlist-card");
				$card_wrapper.addClass("wish-removed");
			};
			let args = { item_code: item_code };
			this.add_remove_from_wishlist("remove", args, success_action, null, true);
		});
	},

	bind_remove_action: function() {
		// remove item from wishlist
		$('.page_content').on("click", ".remove-wish", (e) => {
			const $remove_wish_btn = $(e.currentTarget);
			let item_code = $remove_wish_btn.data("item-code");

			let success_action = function() {
				const $card_wrapper = $remove_wish_btn.closest(".wishlist-card");
				$card_wrapper.addClass("wish-removed");
			};
			let args = { item_code: item_code };
			this.add_remove_from_wishlist("remove", args, success_action);
		});
	},

	bind_wishlist_action() {
		// 'wish'('like') or 'unwish' item in product listing
		$('.page_content').on('click', '.like-action', (e) => {
			const $btn = $(e.currentTarget);
			const $wish_icon = $btn.find('.wish-icon');
			let me = this;

			let success_action = function() {
				erpnext.wishlist.set_wishlist_count();
			};

			if ($wish_icon.hasClass('wished')) {
				// un-wish item
				$btn.removeClass("like-animate");
				this.toggle_button_class($wish_icon, 'wished', 'not-wished');

				let args = { item_code: $btn.data('item-code') };
				let failure_action = function() {
					me.toggle_button_class($wish_icon, 'not-wished', 'wished');
				};
				this.add_remove_from_wishlist("remove", args, success_action, failure_action);
			} else {
				// wish item
				$btn.addClass("like-animate");
				this.toggle_button_class($wish_icon, 'not-wished', 'wished');

				let args = {
					item_code: $btn.data('item-code'),
					price: $btn.data('price'),
					formatted_price: $btn.data('formatted-price')
				};
				let failure_action = function() {
					me.toggle_button_class($wish_icon, 'wished', 'not-wished');
				};
				this.add_remove_from_wishlist("add", args, success_action, failure_action);
			}
		});
	},

	toggle_button_class(button, remove, add) {
		button.removeClass(remove);
		button.addClass(add);
	},

	add_remove_from_wishlist(action, args, success_action, failure_action, async=false) {
		/*	AJAX call to add or remove Item from Wishlist
			action: "add" or "remove"
			args: args for method (item_code, price, formatted_price),
			success_action: method to execute on successs,
			failure_action: method to execute on failure,
			async: make call asynchronously (true/false).	*/
		let method = "erpnext.e_commerce.doctype.wishlist.wishlist.add_to_wishlist";
		if (action === "remove") {
			method = "erpnext.e_commerce.doctype.wishlist.wishlist.remove_from_wishlist";
		}

		frappe.call({
			async: async,
			type: "POST",
			method: method,
			args: args,
			callback: function (r) {
				if (r.exc) {
					if (failure_action && (typeof failure_action === 'function')) {
						failure_action();
					}
					frappe.msgprint({
						message: __("Sorry, something went wrong. Please refresh."),
						indicator: "red", title: __("Note")
					});
				} else if (success_action && (typeof success_action === 'function')) {
					success_action();
				}
			}
		});
	}

});

frappe.ready(function() {
	if (window.location.pathname !== "/wishlist") {
		$(".wishlist").toggleClass('hidden', true);
		wishlist.set_wishlist_count();
	} else {
		wishlist.bind_move_to_cart_action();
		wishlist.bind_remove_action();
	}

});