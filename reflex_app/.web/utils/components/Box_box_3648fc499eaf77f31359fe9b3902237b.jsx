
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_3648fc499eaf77f31359fe9b3902237b = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_d04331f39bea52a415abbd0f96bef6b0 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.go_next_month", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{"aria-label":"Next month",css:({ ["cursor"] : "pointer", ["color"] : "#6868a2", ["padding"] : "8px 10px", ["borderRadius"] : "6px", ["fontSize"] : "16px", ["lineHeight"] : "1", ["&:hover"] : ({ ["color"] : "#818cf8" }) }),onClick:on_click_d04331f39bea52a415abbd0f96bef6b0,role:"button",tabIndex:0},children)
    )
});
