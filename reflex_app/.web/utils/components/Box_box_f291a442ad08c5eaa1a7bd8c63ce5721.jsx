
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_f291a442ad08c5eaa1a7bd8c63ce5721 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_d04331f39bea52a415abbd0f96bef6b0 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.go_next_month", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["cursor"] : "pointer", ["color"] : "#4e4e6a", ["padding"] : "4px 8px", ["borderRadius"] : "6px", ["&:hover"] : ({ ["color"] : "#818cf8", ["background"] : "#1c1c25" }) }),onClick:on_click_d04331f39bea52a415abbd0f96bef6b0},children)
    )
});
