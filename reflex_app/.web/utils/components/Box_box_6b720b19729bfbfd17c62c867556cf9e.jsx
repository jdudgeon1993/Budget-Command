
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_6b720b19729bfbfd17c62c867556cf9e = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_85d27e9aeefd218c061f729fb0e74aac = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.go_prev_month", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{"aria-label":"Previous month",css:({ ["cursor"] : "pointer", ["color"] : "#6868a2", ["padding"] : "8px 10px", ["borderRadius"] : "6px", ["fontSize"] : "16px", ["lineHeight"] : "1", ["&:hover"] : ({ ["color"] : "#818cf8" }) }),onClick:on_click_85d27e9aeefd218c061f729fb0e74aac,role:"button",tabIndex:0},children)
    )
});
